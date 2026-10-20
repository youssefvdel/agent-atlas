#!/usr/bin/env python3
"""
extract_skills.py — walk every SKILL.md on this machine, parse frontmatter + body
structure, and emit a machine-readable skill index.

Outputs (into --out dir):
  skills.raw.json     every skill, full metadata, no taxonomy
  skills.index.json   taxonomy-assigned, grouped, with tree + stats
  skills.index.yaml   same, YAML
  skills.tree.md      rendered markdown tree for humans

Usage:
  python3 tools/extract_skills.py --out data/
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("pyyaml required: pip install pyyaml")

DEFAULT_ROOTS = [
    Path.home() / ".hermes" / "skills",
    Path.home() / ".hermes" / "plugins",
]

# Directory name -> (taxonomy domain, sub-domain). Skills in a category dir
# inherit the domain; the leaf directory is the capability.
DIR_TAXONOMY = {
    "creative": ("creative", "design-and-media"),
    "productivity": ("productivity", "office-and-docs"),
    "software-development": ("engineering", "software-development"),
    "research": ("research", "discovery-and-citation"),
    "media": ("media", "audio-and-social"),
    "email": ("comms", "email-and-messaging"),
    "social-media": ("comms", "email-and-messaging"),
    "note-taking": ("productivity", "office-and-docs"),
    "web": ("engineering", "web-and-network"),
    "autonomous-ai-agents": ("agents", "delegation-and-orchestration"),
    "governance": ("agents", "delegation-and-orchestration"),
}

# Explicit overrides for skills that live at the root of ~/.hermes/skills
# (no category dir) and would otherwise be unclassifiable.
ROOT_OVERRIDES = {
    "algorithmic-art": ("creative", "design-and-media", "generative-art"),
    "apple-design": ("creative", "design-and-media", "design-systems"),
    "brand-guidelines": ("creative", "design-and-media", "design-systems"),
    "browser-automation": ("engineering", "web-and-network", "browser-automation"),
    "browser-file-harvest": ("engineering", "web-and-network", "browser-automation"),
    "canvas-design": ("creative", "design-and-media", "generative-art"),
    "chromium-extension": ("engineering", "web-and-network", "extensions"),
    "frontend-design": ("creative", "design-and-media", "interface-design"),
    "go-cli": ("engineering", "software-development", "cli-tooling"),
    "impeccable": ("creative", "design-and-media", "interface-design"),
    "live-view-flicker": ("engineering", "web-and-network", "performance"),
    "name-availability": ("productivity", "office-and-docs", "naming"),
    "ponytail": ("engineering", "software-development", "code-style"),
    "protocol-translation": ("agents", "delegation-and-orchestration", "provider-adapters"),
    "provider-recon": ("agents", "delegation-and-orchestration", "provider-adapters"),
    "react-best-practices": ("engineering", "software-development", "frontend-frameworks"),
    "recon-pure-vpn": ("engineering", "web-and-network", "networking"),
    "rust-cli": ("engineering", "software-development", "cli-tooling"),
    "stealth-browser": ("engineering", "web-and-network", "browser-automation"),
    "system-architect": ("engineering", "software-development", "architecture"),
    "tauri-live-debug": ("engineering", "desktop-and-mobile", "tauri"),
    "tauri-v2": ("engineering", "desktop-and-mobile", "tauri"),
    "theme-factory": ("creative", "design-and-media", "design-systems"),
    "taste-skill": ("creative", "design-and-media", "interface-design"),
    "ui-ux-craft-kit": ("creative", "design-and-media", "interface-design"),
    "ui-ux-dev-paid": ("creative", "design-and-media", "interface-design"),
    "ui-ux-pro-max-plus": ("creative", "design-and-media", "interface-design"),
    "ux-design-pro-max": ("creative", "design-and-media", "interface-design"),
    "web-design-guidelines": ("creative", "design-and-media", "interface-design"),
    "kowalski-animate": ("creative", "motion", "animation-philosophy"),
    "kowalski-animation-vocabulary": ("creative", "motion", "animation-philosophy"),
    "kowalski-design-eng": ("creative", "motion", "animation-philosophy"),
    "kowalski-improve-animations": ("creative", "motion", "animation-philosophy"),
    "web-design-guidelines": ("creative", "design-and-media", "interface-design"),
    "windows-interop": ("engineering", "desktop-and-mobile", "windows-bridge"),
    "windows-workstation-setup": ("engineering", "desktop-and-mobile", "windows-bridge"),
    "mail-server-ops": ("comms", "email-and-messaging", "mail-infrastructure"),
    "apple-notes": ("productivity", "office-and-docs", "notes-and-reminders"),
    "apple-reminders": ("productivity", "office-and-docs", "notes-and-reminders"),
    "findmy": ("productivity", "office-and-docs", "notes-and-reminders"),
    "imessage": ("comms", "email-and-messaging", "messaging"),
    "sdlc-review": ("engineering", "software-development", "code-quality"),
    "riot-client-api": ("engineering", "web-and-network", "api-clients"),
    "riot-client-local-api": ("engineering", "web-and-network", "api-clients"),
}

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CODE_FENCE_RE = re.compile(r"^```", re.MULTILINE)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = FM_RE.match(text)
    if not m:
        return {}, text
    raw = m.group(1)
    body = text[m.end():]
    try:
        data = yaml.safe_load(raw) or {}
    except Exception:
        data = {}
        for line in raw.splitlines():
            if ":" in line and not line.startswith((" ", "-", "\t")):
                k, _, v = line.partition(":")
                data[k.strip()] = v.strip().strip('"\'')
    if not isinstance(data, dict):
        data = {}
    return data, body


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "untitled"


def extract_skill(path: Path, root: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    fm, body = parse_frontmatter(text)
    rel = path.relative_to(root)

    parts = list(rel.parts)          # e.g. ["creative", "manim-video", "SKILL.md"]
    dirs = parts[:-1]
    leaf_dir = dirs[-1] if dirs else ""

    # skill identity
    name = str(fm.get("name") or (leaf_dir or path.parent.name))
    desc = str(fm.get("description") or "").strip()

    # linked files (references/, scripts/, assets/, templates/)
    linked = []
    skill_dir = path.parent
    for sub in ("references", "scripts", "assets", "templates"):
        d = skill_dir / sub
        if d.is_dir():
            for f in sorted(d.rglob("*")):
                if f.is_file():
                    linked.append(
                        {
                            "path": str(f.relative_to(skill_dir)),
                            "bytes": f.stat().st_size,
                        }
                    )

    # body structure
    headings = re.findall(r"^(#{2,3})\s+(.+)$", body, re.MULTILINE)
    h2 = [h[1].strip() for h in headings if h[0] == "##"]
    h3 = [h[1].strip() for h in headings if h[0] == "###"]
    code_blocks = len(CODE_FENCE_RE.findall(body))
    body_links = [u for _, u in LINK_RE.findall(body) if u.startswith("http")]

    # taxonomy
    # nested layout: <category>/<skill>/SKILL.md  -> category decides domain
    # flat layout:   <skill>/SKILL.md            -> ROOT_OVERRIDES decides
    if len(dirs) >= 2:
        category_dir = dirs[0]
        if category_dir in DIR_TAXONOMY:
            domain, subdomain = DIR_TAXONOMY[category_dir]
            capability = leaf_dir
        else:
            domain, subdomain, capability = "unclassified", "unclassified", leaf_dir
    elif leaf_dir in ROOT_OVERRIDES:
        domain, subdomain, capability = ROOT_OVERRIDES[leaf_dir]
        category_dir = "root"
    else:
        domain, subdomain, capability = "unclassified", "unclassified", leaf_dir or name
        category_dir = "root"

    return {
        "name": name,
        "slug": slugify(name),
        "description": desc,
        "description_len": len(desc),
        "path": str(path),
        "relative_path": str(rel),
        "dir": leaf_dir,
        "category_dir": category_dir,
        "frontmatter": {
            k: v for k, v in fm.items() if k not in ("name", "description")
        },
        "allowed_tools": fm.get("allowed-tools") or fm.get("allowed_tools"),
        "license": fm.get("license"),
        "metadata": fm.get("metadata") or {},
        "body": {
            "chars": len(body),
            "lines": body.count("\n") + 1,
            "h2": h2,
            "h3": h3,
            "code_blocks": code_blocks,
            "external_links": sorted(set(body_links)),
        },
        "linked_files": linked,
        "taxonomy": {
            "domain": domain,
            "subdomain": subdomain,
            "capability": capability,
        },
    }


def walk(roots: list[Path]) -> list[tuple[Path, Path]]:
    """Return (skill_md_path, root) pairs."""
    out = []
    for root in roots:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("SKILL.md")):
            # skip nested venvs / node_modules / backups
            parts = set(p.parts)
            if parts & {"node_modules", ".git", "site-packages", "__pycache__", ".venv"}:
                continue
            out.append((p, root))
    return out


def build_index(skills: list[dict]) -> dict:
    tree: dict = {}
    for s in skills:
        t = s["taxonomy"]
        tree.setdefault(t["domain"], {}).setdefault(t["subdomain"], {}).setdefault(
            t["capability"], []
        ).append(s["name"])

    stats = {
        "total": len(skills),
        "domains": len(tree),
        "with_links": sum(1 for s in skills if s["body"]["external_links"]),
        "with_code": sum(1 for s in skills if s["body"]["code_blocks"]),
        "total_code_blocks": sum(s["body"]["code_blocks"] for s in skills),
        "total_body_chars": sum(s["body"]["chars"] for s in skills),
        "total_linked_files": sum(len(s["linked_files"]) for s in skills),
        "avg_description_len": round(
            sum(s["description_len"] for s in skills) / max(1, len(skills)), 1
        ),
    }
    return {"tree": tree, "stats": stats}


def render_tree_md(index: dict, skills: list[dict]) -> str:
    by_name = {s["name"]: s for s in skills}
    tree = index["tree"]
    stats = index["stats"]
    L: list[str] = []
    L.append("# Skill hierarchy")
    L.append("")
    L.append(
        f"_{stats['total']} skills · {stats['domains']} domains · "
        f"{stats['total_code_blocks']} code blocks · "
        f"{stats['total_linked_files']} linked files · "
        f"{stats['total_body_chars']:,} body chars_"
    )
    L.append("")

    def walk_tree(node: dict, depth: int, path: list[str]) -> None:
        for key in sorted(node):
            val = node[key]
            if isinstance(val, list):
                for name in sorted(val):
                    s = by_name.get(name, {})
                    desc = (s.get("description") or "").split(".")[0]
                    if len(desc) > 96:
                        desc = desc[:93] + "..."
                    L.append(
                        f"{'  ' * depth}- **{key}** → `{name}`"
                        + (f" — {desc}" if desc else "")
                    )
            else:
                L.append(f"{'  ' * depth}- **{key}**")
                walk_tree(val, depth + 1, path + [key])

    walk_tree(tree, 0, [])
    L.append("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    ap.add_argument("--roots", nargs="*", default=None)
    args = ap.parse_args()

    roots = [Path(p).expanduser() for p in args.roots] if args.roots else DEFAULT_ROOTS
    pairs = walk(roots)

    skills = []
    seen: set[tuple[str, str]] = set()
    for path, root in pairs:
        s = extract_skill(path, root)
        if not s:
            continue
        key = (s["name"], s["path"])
        if key in seen:
            continue
        seen.add(key)
        skills.append(s)

    # de-dup by name, keeping the richest copy (most body chars)
    best: dict[str, dict] = {}
    for s in skills:
        cur = best.get(s["name"])
        if cur is None or s["body"]["chars"] > cur["body"]["chars"]:
            best[s["name"]] = s
    skills = sorted(best.values(), key=lambda s: (s["taxonomy"]["domain"], s["taxonomy"]["capability"], s["name"]))

    index = build_index(skills)
    index["generated_at"] = datetime.now(timezone.utc).isoformat()
    index["roots"] = [str(r) for r in roots]

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    (out / "skills.raw.json").write_text(
        json.dumps(skills, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out / "skills.index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out / "skills.index.yaml").write_text(
        yaml.safe_dump(index, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )
    (out / "skills.tree.md").write_text(
        render_tree_md(index, skills), encoding="utf-8"
    )

    print(f"skills extracted : {len(skills)}")
    print(f"domains          : {index['stats']['domains']}")
    print(f"code blocks      : {index['stats']['total_code_blocks']}")
    print(f"linked files     : {index['stats']['total_linked_files']}")
    print(f"written          : {out.resolve()}")


if __name__ == "__main__":
    main()
