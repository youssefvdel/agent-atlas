#!/usr/bin/env python3
"""
scrape_libs.py — pull live, verifiable metadata for a catalog of npm/GitHub
libraries from the npm registry + GitHub API. No invented numbers: every field
comes from a real HTTP response, and failures are recorded as errors.

Usage:
  python3 tools/scrape_libs.py --spec data/libs.spec.json --out data/libs.live.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = "agent-atlas-scraper/1.0 (+https://github.com/youssefvdel)"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def http_json(url: str, headers: dict | None = None, retries: int = 3) -> dict:
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        h.update(headers)
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last = e
            if isinstance(e, urllib.error.HTTPError) and e.code in (403, 404, 451):
                break
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"{url} -> {last}")


def npm_info(pkg: str) -> dict:
    d = http_json(f"https://registry.npmjs.org/{pkg.replace('/', '%2f')}")
    latest = d.get("dist-tags", {}).get("latest", "")
    v = d.get("versions", {}).get(latest, {}) if latest else {}
    times = d.get("time", {})
    return {
        "npm_package": pkg,
        "npm_latest": latest,
        "npm_latest_published": times.get(latest),
        "npm_created": times.get("created"),
        "npm_modified": times.get("modified"),
        "npm_license": v.get("license"),
        "npm_description": (d.get("description") or "")[:400],
        "npm_dependencies": len(v.get("dependencies") or {}),
        "npm_peer_dependencies": list((v.get("peerDependencies") or {}).keys()),
        "npm_unpacked_size": v.get("dist", {}).get("unpackedSize"),
        "npm_engines": v.get("engines"),
        "npm_repository": (v.get("repository") or {}).get("url") if isinstance(v.get("repository"), dict) else v.get("repository"),
        "npm_homepage": v.get("homepage"),
        "npm_keywords": (v.get("keywords") or [])[:12],
    }


def github_info(repo: str) -> dict:
    h = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    d = http_json(f"https://api.github.com/repos/{repo}", headers=h)
    return {
        "repo": repo,
        "repo_full_name": d.get("full_name"),
        "repo_description": d.get("description"),
        "stars": d.get("stargazers_count"),
        "forks": d.get("forks_count"),
        "open_issues": d.get("open_issues_count"),
        "license": (d.get("license") or {}).get("spdx_id"),
        "language": d.get("language"),
        "topics": d.get("topics", []),
        "homepage": d.get("homepage"),
        "archived": d.get("archived"),
        "pushed_at": d.get("pushed_at"),
        "created_at": d.get("created_at"),
        "default_branch": d.get("default_branch"),
    }


def npm_downloads(pkg: str) -> dict:
    """last-week downloads from the npm API."""
    try:
        d = http_json(f"https://api.npmjs.org/downloads/point/last-week/{pkg}")
        return {"downloads_last_week": d.get("downloads")}
    except Exception as e:
        return {"downloads_last_week": None, "downloads_error": str(e)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    libs = spec["libraries"] if isinstance(spec, dict) else spec

    results = []
    for i, entry in enumerate(libs, 1):
        name = entry.get("name", "?")
        row: dict = {"name": name, "errors": []}
        pkg = entry.get("npm")
        repo = entry.get("repo")
        if pkg:
            try:
                row.update(npm_info(pkg))
            except Exception as e:
                row["errors"].append(f"npm:{e}")
        else:
            row["errors"].append("npm:no-package-specified")
        if repo:
            try:
                row.update(github_info(repo))
            except Exception as e:
                row["errors"].append(f"github:{e}")
        else:
            row["errors"].append("github:no-repo-specified")
        if pkg and entry.get("track_downloads", True):
            row.update(npm_downloads(pkg))
        row["category"] = entry.get("category")
        row["tags"] = entry.get("tags", [])
        row["notes"] = entry.get("notes", "")
        results.append(row)
        print(
            f"[{i}/{len(libs)}] {name:32} "
            f"npm={row.get('npm_latest','-'):>10} "
            f"stars={row.get('stars','-'):>7} "
            f"dl/wk={row.get('downloads_last_week','-')}",
            file=sys.stderr,
        )
        time.sleep(0.35)  # be polite to both APIs

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_spec": args.spec,
        "count": len(results),
        "libraries": results,
    }
    Path(args.out).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    ok = sum(1 for r in results if not r["errors"])
    print(f"\n{ok}/{len(results)} entries fully resolved -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
