#!/usr/bin/env python3
"""
resolve_spec.py — repair a library spec in place.

For every entry whose npm package or GitHub repo fails to resolve:
  1. npm package wrong/404 -> query the npm search API for the closest real
     package name, and adopt its canonical `repository` URL.
  2. GitHub repo wrong/404 -> take the repo from the npm package's own
     `repository` field (authoritative), else search GitHub by package name.
  3. Repo casing/renames -> GitHub 301/redirect is followed by urllib, but a
     renamed org gives 404; fall back to the npm repository field.

Writes a repaired spec plus a report of what changed and what is still broken.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "agent-atlas-resolver/1.0"
GITHUB_TOKEN = None


def http_json(url: str, headers: dict | None = None, retries: int = 2) -> dict:
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        h.update(headers)
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            last = e
            code = getattr(e, "code", None)
            if code in (403, 404, 451):
                break
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(str(last))


def gh_headers() -> dict:
    return {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}


def npm_exists(pkg: str) -> bool:
    try:
        http_json(f"https://registry.npmjs.org/{urllib.parse.quote(pkg, safe='')}")
        return True
    except Exception:
        return False


def npm_repo(pkg: str) -> str | None:
    try:
        d = http_json(f"https://registry.npmjs.org/{urllib.parse.quote(pkg, safe='')}")
    except Exception:
        return None
    latest = d.get("dist-tags", {}).get("latest")
    v = d.get("versions", {}).get(latest, {}) if latest else {}
    repo = v.get("repository") or d.get("repository")
    url = None
    if isinstance(repo, dict):
        url = repo.get("url")
    elif isinstance(repo, str):
        url = repo
    if not url:
        return None
    url = re.sub(r"^git\+", "", url)
    url = re.sub(r"\.git$", "", url)
    m = re.search(r"github\.com[:/]+([^/]+)/([^/]+)", url, re.I)
    if not m:
        return None
    return f"{m.group(1)}/{m.group(2).rstrip('/')}"


def gh_exists(repo: str) -> bool:
    try:
        http_json(f"https://api.github.com/repos/{repo}", headers=gh_headers())
        return True
    except Exception:
        return False


def gh_search_repo(query: str) -> str | None:
    try:
        d = http_json(
            f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort=stars&per_page=3",
            headers=gh_headers(),
        )
    except Exception:
        return None
    items = d.get("items") or []
    return items[0].get("full_name") if items else None


def npm_search(name: str) -> list[str]:
    try:
        d = http_json(
            f"https://registry.npmjs.org/-/v1/search?text={urllib.parse.quote(name)}&size=8"
        )
    except Exception:
        return []
    out = []
    for o in d.get("objects", []):
        pkg = o.get("package", {})
        out.append(
            {
                "name": pkg.get("name"),
                "version": pkg.get("version"),
                "description": (pkg.get("description") or "")[:120],
                "score": (o.get("score") or {}).get("final"),
            }
        )
    return out


def main() -> None:
    global GITHUB_TOKEN
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    import os

    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    libs = spec["libraries"] if isinstance(spec, dict) else spec

    changes = []
    unresolved = []

    for entry in libs:
        name = entry.get("name", "?")
        pkg = entry.get("npm")
        repo = entry.get("repo")

        # --- fix npm package -------------------------------------------------
        if pkg and not npm_exists(pkg):
            cands = npm_search(name.replace(" (legacy)", "").replace(" (npm alt)", "").strip())
            best = None
            for c in cands:
                if not c["name"]:
                    continue
                # prefer exact-ish name match
                if c["name"].lower() == name.lower().replace(" ", "-"):
                    best = c
                    break
                if best is None:
                    best = c
            if best:
                changes.append(
                    {
                        "name": name,
                        "field": "npm",
                        "from": pkg,
                        "to": best["name"],
                        "via": f"npm search: {best['description']}",
                    }
                )
                entry["npm"] = best["name"]
                pkg = best["name"]
            else:
                unresolved.append({"name": name, "field": "npm", "tried": pkg})
                entry["npm"] = None
                pkg = None

        # --- fix repo --------------------------------------------------------
        if repo and not gh_exists(repo):
            candidate = None
            via = None
            if pkg:
                candidate = npm_repo(pkg)
                if candidate:
                    via = f"npm registry repository field of {pkg}"
            if not candidate:
                q = (pkg or name).split("/")[-1].replace("-", " ")
                candidate = gh_search_repo(q)
                via = f"github search: {q}"
            if candidate and gh_exists(candidate):
                changes.append(
                    {"name": name, "field": "repo", "from": repo, "to": candidate, "via": via}
                )
                entry["repo"] = candidate
                repo = candidate
            else:
                unresolved.append(
                    {"name": name, "field": "repo", "tried": [repo, candidate], "via": via}
                )
                entry["repo"] = None

    out = {"libraries": libs} if not isinstance(spec, dict) else {**spec, "libraries": libs}
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    report = {"changes": changes, "unresolved": unresolved}
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"fixed     : {len(changes)}", file=sys.stderr)
    for c in changes:
        print(f"  {c['name']:32} {c['field']:4} {c['from']} -> {c['to']}", file=sys.stderr)
    print(f"unresolved: {len(unresolved)}", file=sys.stderr)
    for u in unresolved:
        print(f"  {u['name']:32} {u['field']:4} tried={u.get('tried')}", file=sys.stderr)


if __name__ == "__main__":
    main()
