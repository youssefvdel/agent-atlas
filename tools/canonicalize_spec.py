#!/usr/bin/env python3
"""
canonicalize_spec.py — for every entry, pull the authoritative repo URL out of
the npm registry's own `repository` field and overwrite a hand-guessed repo.

npm's repository field is the single most reliable source for "where does this
package actually live" — it survives org renames, which is why hand-guessed
GitHub URLs 404. Also verifies each package exists and reports orphan cases
(package missing OR repo missing) for manual triage.
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

UA = "agent-atlas-canonicalize/1.0"
GH_TOKEN = None


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
            if getattr(e, "code", None) in (403, 404, 451):
                break
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(str(last))


def gh_headers() -> dict:
    return {"Authorization": f"token {GH_TOKEN}"} if GH_TOKEN else {}


def npm_meta(pkg: str) -> dict | None:
    try:
        d = http_json(f"https://registry.npmjs.org/{urllib.parse.quote(pkg, safe='')}")
    except Exception:
        return None
    latest = d.get("dist-tags", {}).get("latest")
    v = d.get("versions", {}).get(latest, {}) if latest else {}
    repo = v.get("repository") or d.get("repository")
    url = repo.get("url") if isinstance(repo, dict) else repo
    repo_slug = None
    if isinstance(url, str):
        u = re.sub(r"^git\+", "", url).removesuffix(".git")
        m = re.search(r"github\.com[:/]+([^/]+)/([^/#?]+)", u, re.I)
        if m:
            repo_slug = f"{m.group(1)}/{m.group(2)}"
    return {
        "latest": latest,
        "license": v.get("license"),
        "description": (d.get("description") or "")[:200],
        "homepage": v.get("homepage"),
        "repo_slug": repo_slug,
        "deps": len(v.get("dependencies") or {}),
        "unpacked": v.get("dist", {}).get("unpackedSize"),
    }


def gh_ok(repo: str) -> bool:
    try:
        http_json(f"https://api.github.com/repos/{repo}", headers=gh_headers())
        return True
    except Exception:
        return False


def main() -> None:
    global GH_TOKEN
    import os

    GH_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--apply", action="store_true", help="overwrite repo from npm registry field")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    libs = spec["libraries"] if isinstance(spec, dict) else spec

    changed, orphans = [], []
    for entry in libs:
        name = entry.get("name", "?")
        pkg = entry.get("npm")
        if not pkg:
            orphans.append({"name": name, "why": "no-npm-package", "repo": entry.get("repo")})
            continue
        meta = npm_meta(pkg)
        if meta is None:
            orphans.append({"name": name, "why": f"npm-404:{pkg}", "repo": entry.get("repo")})
            continue
        entry["npm_description"] = meta["description"]
        entry["npm_homepage"] = meta["homepage"]
        entry["npm_repo_slug"] = meta["repo_slug"]
        canonical = meta["repo_slug"]
        current = entry.get("repo")
        if canonical and canonical.lower() != (current or "").lower():
            changed.append({"name": name, "from": current, "to": canonical})
            if args.apply:
                entry["repo"] = canonical
        if not entry.get("repo") and canonical:
            entry["repo"] = canonical
        elif not entry.get("repo"):
            orphans.append({"name": name, "why": "no-repo", "npm": pkg})
        time.sleep(0.15)

    out = {**spec, "libraries": libs} if isinstance(spec, dict) else libs
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"repo changes : {len(changed)}", file=sys.stderr)
    for c in changed:
        print(f"  {c['name']:32} {c['from']} -> {c['to']}", file=sys.stderr)
    print(f"orphans      : {len(orphans)}", file=sys.stderr)
    for o in orphans:
        print(f"  {o['name']:32} {o['why']}", file=sys.stderr)


if __name__ == "__main__":
    main()
