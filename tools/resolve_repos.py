#!/usr/bin/env python3
"""
resolve_repos.py — pick the canonical GitHub repo for each npm package.

Decision order (and why):

  1. **npm's `repository` field wins.** It is written by the package's own
     maintainer, so it is the most authoritative pointer there is. It is only
     overridden when the target is a *fork* (npm sometimes points at a
     personal fork — danielkalen/greensock, pshihn/rough, dmiller9911/react-bits);
     in that case GitHub's `parent`/`source` field is followed upstream.

  2. **If the npm field 404s** (repo renamed, deleted, or the package moved),
     fall back to GitHub search by package name and take the best non-fork,
     non-archived candidate whose repo name matches the package leaf.

  3. The repo's own root `package.json` name is recorded as *evidence* but is
     never a hard gate: monorepos publish under a family name
     (`motion-one`, `root`, `definitely-typed`, `remotion-monorepo`,
     `react-spring--root`, `@zag-js/org`), so it would reject valid matches.

Every API response is cached in data/.apicache.json.
"""
from __future__ import annotations

import argparse
import base64
import difflib
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

UA = "agent-atlas-resolve-repos/5.0"
GH_TOKEN = None
CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / ".apicache.json"
_cache: dict[str, str | None] = {}
_cache_lock = threading.Lock()
_cache_loaded = False


def load_cache() -> None:
    global _cache_loaded
    if _cache_loaded:
        return
    if CACHE_PATH.exists():
        try:
            _cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            _cache = {}
    _cache_loaded = True


def save_cache() -> None:
    with _cache_lock:
        CACHE_PATH.write_text(json.dumps(_cache, indent=1), encoding="utf-8")


def http_json(url: str, headers: dict | None = None, retries: int = 3, raw: bool = False):
    load_cache()
    with _cache_lock:
        if url in _cache:
            cached = _cache[url]
            if cached is not None:
                try:
                    return cached if raw else json.loads(cached)
                except Exception:
                    pass
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        h.update(headers)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=25) as r:
                body = r.read().decode("utf-8", "replace")
                with _cache_lock:
                    _cache[url] = body
                return body if raw else json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code == 403:
                reset = e.headers.get("X-RateLimit-Reset")
                if reset:
                    wait = max(0, int(reset) - int(time.time())) + 2
                    if wait < 120:
                        time.sleep(wait)
                        continue
                break
            if e.code in (404, 451):
                break
            time.sleep(1.2 * (attempt + 1))
        except Exception:
            time.sleep(1.2 * (attempt + 1))
    with _cache_lock:
        _cache[url] = None
    return None


def gh_headers() -> dict:
    return {"Authorization": f"token {GH_TOKEN}"} if GH_TOKEN else {}


def gh_repo(slug: str) -> dict | None:
    d = http_json(f"https://api.github.com/repos/{slug}", headers=gh_headers())
    if not d or d.get("message"):
        return None
    return d


def gh_search(query: str, per_page: int = 10) -> list[dict]:
    d = http_json(
        f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort=stars&per_page={per_page}",
        headers=gh_headers(),
    )
    if not d or d.get("message"):
        return []
    return d.get("items", [])


def repo_package_name(full: str) -> str | None:
    d = http_json(
        f"https://api.github.com/repos/{full}/contents/package.json",
        headers=gh_headers(),
        raw=True,
    )
    if not d:
        return None
    try:
        return json.loads(base64.b64decode(d).decode("utf-8", "replace")).get("name")
    except Exception:
        return None


def npm_meta(pkg: str) -> dict | None:
    d = http_json(f"https://registry.npmjs.org/{urllib.parse.quote(pkg, safe='')}")
    if not d:
        return None
    latest = d.get("dist-tags", {}).get("latest")
    v = d.get("versions", {}).get(latest, {}) if latest else {}
    repo = v.get("repository") or d.get("repository")
    url = repo.get("url") if isinstance(repo, dict) else repo
    slug = None
    if isinstance(url, str):
        u = re.sub(r"^git\+", "", url).removesuffix(".git")
        m = re.search(r"github\.com[:/]+([^/]+)/([^/#?]+)", u, re.I)
        if m:
            slug = f"{m.group(1)}/{m.group(2)}"
    return {"latest": latest, "repo_slug": slug}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def search_score(pkg: str, cand: dict) -> float:
    """Rank a GitHub search result for a package we could not link via npm."""
    leaf = norm(pkg.split("/")[-1])
    repo_leaf = norm(cand["full_name"].split("/")[-1])
    s = 0.0
    s += min(cand.get("stargazers_count", 0), 120000) / 100.0
    if not cand.get("fork"):
        s += 60.0
    if cand.get("archived"):
        s -= 50.0
    if repo_leaf == leaf:
        s += 70.0
    else:
        s += difflib.SequenceMatcher(None, leaf, repo_leaf).ratio() * 30.0
    scope = pkg.split("/")[0][1:] if pkg.startswith("@") else None
    if scope and scope.lower() in cand["full_name"].lower():
        s += 25.0
    desc = (cand.get("description") or "").lower()
    if leaf and leaf[:6] in re.sub(r"[^a-z0-9]", "", desc):
        s += 12.0
    return s


def resolve_one(pkg: str, recorded: str | None) -> tuple[str | None, dict]:
    meta = npm_meta(pkg)
    npm_slug = meta.get("repo_slug") if meta else None
    info: dict = {"npm_field": npm_slug, "method": None}

    # ---- rule 1: npm repository field -----------------------------------
    npm_stars = 0
    if npm_slug:
        r = gh_repo(npm_slug)
        if r:
            npm_stars = r.get("stargazers_count", 0)
            if r.get("fork"):
                # follow upstream
                for key in ("parent", "source"):
                    up = r.get(key)
                    if up and up.get("full_name"):
                        ur = gh_repo(up["full_name"])
                        if ur and not ur.get("fork"):
                            info["method"] = f"npm-field/fork->{up['full_name']}"
                            info["fork_upstream"] = f"{npm_slug} -> {up['full_name']}"
                            return up["full_name"], {
                                **info,
                                "stars": ur.get("stargazers_count", 0),
                                "repo_pkgname": repo_package_name(up["full_name"]),
                            }
            else:
                info["npm_field_stars"] = npm_stars

    # ---- rule 1b: a recorded canonical repo beats a low-signal npm field --
    #     Some packages' npm `repository` field points at an impersonator or a
    #     personal copy with ~0 stars (dmiller9911/react-bits has 5★,
    #     Shi-Dekai/origin-ui has 0★, while the real projects have 49k and
    #     10k). When the spec records a repo whose stars clearly outrank the
    #     npm field, prefer it.
    if recorded and recorded != npm_slug:
        rr = gh_repo(recorded)
        if rr and not rr.get("fork") and not rr.get("archived"):
            rec_stars = rr.get("stargazers_count", 0)
            if npm_stars == 0 or rec_stars > npm_stars * 3:
                info["method"] = "recorded(canonical)"
                info["beat_npm_field"] = f"{recorded} star-{rec_stars} > npm-field star-{npm_stars}"
                return recorded, {
                    **info,
                    "stars": rec_stars,
                    "repo_pkgname": repo_package_name(recorded),
                }

    if npm_slug and info.get("npm_field_stars") is not None:
        info["method"] = "npm-field"
        return npm_slug, {
            **info,
            "stars": npm_stars,
            "repo_pkgname": repo_package_name(npm_slug),
        }

    # ---- rule 3: GitHub search -------------------------------------------
    leaf = pkg.split("/")[-1]
    cands: dict[str, dict] = {}
    for q in (f"{leaf} in:name", f"{leaf.replace('-', ' ')} in:name"):
        for r in gh_search(q):
            full = r.get("full_name")
            if full and full not in cands:
                cands[full] = r
    pool = {k: v for k, v in cands.items() if not v.get("fork") and not v.get("archived")}
    if not pool:
        pool = cands
    if not pool:
        return None, {**info, "candidates": []}

    ranked = sorted(pool.values(), key=lambda c: search_score(pkg, c), reverse=True)
    winner = ranked[0]
    info["method"] = "github-search"
    return winner["full_name"], {
        **info,
        "stars": winner.get("stargazers_count", 0),
        "repo_pkgname": repo_package_name(winner["full_name"]),
        "runner_up": ranked[1]["full_name"] if len(ranked) > 1 else None,
    }


def main() -> None:
    global GH_TOKEN
    GH_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    libs = spec["libraries"] if isinstance(spec, dict) else spec

    # GitHub repo names are case-insensitive: Mattpocock/skills and
    # mattpocock/skills are the same repo. Dedupe case-insensitively, keeping
    # whichever entry carries more metadata.
    by_repo: dict[str, dict] = {}
    ordered: list[dict] = []
    for e in libs:
        r = (e.get("repo") or "").lower()
        if not r:
            ordered.append(e)
            continue
        if r not in by_repo:
            by_repo[r] = e
            ordered.append(e)
            continue
        prev = by_repo[r]
        score = lambda x: (1 if x.get("npm") else 0) + len(str(x.get("notes") or ""))
        if score(e) > score(prev):
            ordered[ordered.index(prev)] = e
            by_repo[r] = e
    libs = ordered

    pkgs: dict[str, str | None] = {}
    for e in libs:
        p = e.get("npm")
        if p and p not in pkgs:
            pkgs[p] = e.get("repo")

    print(f"resolving {len(pkgs)} unique packages...", file=sys.stderr)
    t0 = time.time()
    results: dict[str, tuple[str | None, dict]] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(resolve_one, p, r): p for p, r in pkgs.items()}
        for fut in futs:
            pass
        for fut, p in futs.items():
            results[p] = fut.result()
    save_cache()

    changed, unresolved = [], []
    for e in libs:
        p = e.get("npm")
        if not p:
            if e.get("repo"):
                r = gh_repo(e["repo"])
                if r:
                    e["repo_stars"] = r.get("stargazers_count")
                    e["repo_resolution"] = "manual"
                    e["verified_pkg_name"] = repo_package_name(e["repo"])
                    continue
            unresolved.append({"name": e.get("name"), "pkg": None, "why": "no-npm-and-no-repo"})
            continue
        winner, meta = results.get(p, (None, {}))
        if not winner:
            unresolved.append({"name": e.get("name"), "pkg": p, **meta})
            continue
        if e.get("repo") != winner:
            changed.append(
                {"name": e.get("name"), "pkg": p, "from": e.get("repo"), "to": winner, **meta}
            )
        e["repo"] = winner
        e["repo_stars"] = meta.get("stars")
        e["repo_resolution"] = meta.get("method")
        e["verified_pkg_name"] = meta.get("repo_pkgname")

    out = {**spec, "libraries": libs} if isinstance(spec, dict) else libs
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nresolved    : {len(pkgs) - len(unresolved)}/{len(pkgs)}  ({time.time()-t0:.0f}s)")
    print(f"repo changes: {len(changed)}")
    for c in changed:
        print(f"  {c['name']:28} {str(c['from']):26} -> {c['to']:30} ★{str(c.get('stars')):<7} via={c.get('method')}")
    print(f"unresolved  : {len(unresolved)}")
    for u in unresolved:
        print(f"  {u['name']:28} {u.get('pkg')}")


if __name__ == "__main__":
    main()
