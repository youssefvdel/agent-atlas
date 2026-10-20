#!/usr/bin/env python3
"""
build_site.py — generate the interactive atlas browser (site/index.html) plus
the per-domain documentation pages under docs/.

Everything rendered comes from the generated data files:
  data/skills.index.json   the skill hierarchy
  data/libs.live.json      the library catalog with live metadata
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
VERIFIED_ON = "2026-10-20"
SITE = ROOT / "site"

CATEGORY_BLURBS = {
    "animation-core": "The engines. GSAP for timelines, Motion for React, anime.js for vanilla.",
    "scroll-and-reveal": "Smooth scrolling and scroll-triggered reveals.",
    "carousel-and-ui": "Carousels, drawers, sheets.",
    "gesture-and-drag": "Pointer, drag, pinch, reorder.",
    "lottie-and-rive": "Designer-exported and interactive runtime animation.",
    "page-transitions": "Route and page transitions.",
    "creative-and-3d": "Three.js, R3F, PixiJS, shaders.",
    "data-and-visualization": "Charts and graphs.",
    "text-and-svg": "Text splitting, SVG drawing, hand-drawn type.",
    "code-to-video": "Render video from code, capture frames from a page.",
    "design-skills": "Agent skills that change design output quality.",
    "ux-craft-2026": "The carefully-made web repos of 2026.",
    "creative-craft": "Isometric illustration, shaders, doodles, icons.",
    "tiktok-pushed": "What the design crowd is pushing right now.",
}

CATEGORY_LABELS = {
    "animation-core": "Animation core",
    "scroll-and-reveal": "Scroll & reveal",
    "page-transitions": "Page transitions",
    "carousel-and-ui": "Carousel & UI",
    "gesture-and-drag": "Gesture & drag",
    "text-and-svg": "Text & SVG",
    "data-and-visualization": "Data & visualization",
    "creative-and-3d": "Creative & 3D",
    "lottie-and-rive": "Lottie & Rive",
    "code-to-video": "Code → video",
    "creative-craft": "Creative craft (GitHub)",
    "design-skills": "AI design skills",
    "ux-craft-2026": "High-craft web 2026",
    "tiktok-pushed": "Pushed on TikTok",
}

DOMAIN_LABELS = {
    "creative": "Creative & design",
    "engineering": "Engineering",
    "productivity": "Productivity",
    "research": "Research",
    "comms": "Communication",
    "agents": "Agents & orchestration",
    "media": "Media",
    "unclassified": "Unclassified",
}


def load(name: str):
    p = DATA / name
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def fmt(n) -> str:
    if n is None:
        return "—"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def bytes_fmt(n) -> str:
    if not n:
        return "—"
    if n >= 1_048_576:
        return f"{n / 1_048_576:.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} B"


def build_libs_payload(libs: list[dict]) -> dict:
    out = []
    for l in libs:
        # The scraper's raw field names are npm_package / npm_latest /
        # downloads_last_week. The site reads short names, so map them
        # explicitly — guessing the key silently produced an empty
        # "npm" column for every row.
        pkg = l.get("npm_package") or l.get("npm")
        version = l.get("npm_latest") or l.get("version")
        dl = l.get("downloads_last_week")
        if dl is None:
            dl = l.get("dl")
        npm_license = l.get("npm_license")
        desc = l.get("npm_description") or l.get("repo_description")
        homepage = l.get("npm_homepage") or l.get("homepage")
        out.append(
            {
                "name": l.get("name"),
                "npm": pkg,
                "repo": l.get("repo"),
                "category": l.get("category"),
                "tags": l.get("tags", []),
                "notes": l.get("notes", ""),
                "stars": l.get("stars"),
                "forks": l.get("forks"),
                "dl": dl,
                "version": version,
                "published": l.get("npm_latest_published") or l.get("published"),
                "license": npm_license or l.get("license"),
                "description": desc,
                "homepage": homepage,
                "unpacked": l.get("npm_unpacked_size") or l.get("unpacked"),
                "deps": l.get("npm_dependencies") or l.get("deps"),
                "pushed": l.get("pushed_at") or l.get("pushed"),
                "archived": l.get("archived"),
                "errors": l.get("errors", []),
            }
        )
    return {"libraries": out}


DOC_MANIFEST = [
    # (path, group, title, blurb)
    ("docs/README.md", "Index", "Documentation index", "Everything, and the three findings worth knowing first"),
    ("docs/start-here.md", "Start here", "Start here", "The 2026 stack in one page: what to install, what is hype, what is real"),
    ("docs/libraries/before-you-start.md", "Start here", "Before you start", "Which library for which job — CSS-first routing tables and anti-patterns"),
    ("docs/ecosystem/claude-code-tooling.md", "Start here", "Claude Code tooling", "The 5-minute baseline setup, the decision table, and the pitfalls"),
    ("docs/ecosystem/design-skills.md", "Start here", "AI design skills", "Which design skills are real, ranked by installs rather than stars"),
    ("docs/libraries/animation-libraries.md", "Libraries", "Animation libraries", "50 libraries with real API signatures from the shipped .d.ts files"),
    ("docs/libraries/modern-css.md", "Libraries", "Modern CSS 2026", "What CSS can do natively, verified against MDN browser-compat-data"),
    ("docs/libraries/code-video.md", "Libraries", "Code to video", "41 tools; 22 experiments actually run on this machine"),
    ("docs/libraries/creative-libs.md", "Libraries", "Creative craft repos", "67 hairline-class repos with live stars and install commands"),
    ("docs/libraries/ux-craft-2026.md", "Libraries", "High-craft web 2026", "The repos worth reading the source of, tiered by craft"),
    ("docs/libraries/anchor-hairline.md", "Libraries", "Anchor: hairline", "The reference repo, fully documented"),
    ("docs/libraries/hairline-design-study.md", "Libraries", "The ten rules", "Design rules for pointer-reactive interface figures"),
    ("docs/ecosystem/agent-skills-ecosystem.md", "Ecosystem", "Agent skills ecosystem", "The spec, client conventions, MCP registries, verified repos"),
    ("docs/ecosystem/youtube-design.md", "Ecosystem", "YouTube: AI design", "80 verified videos and the concrete techniques each teaches"),
    ("docs/ecosystem/tiktok-hyped.md", "Ecosystem", "TikTok: the hype", "What is actually being hyped, and which claims are substance"),
    ("docs/skills/spec-compliance.md", "This machine", "Skill spec compliance", "Which skills violate the spec, and which fields are portable"),
    ("data/skills.tree.md", "This machine", "Skill tree", "The rendered hierarchy of all 110 installed skills"),
]


def build_doc_manifest() -> list[dict]:
    out = []
    for rel, group, title, blurb in DOC_MANIFEST:
        p = ROOT / rel
        if not p.exists():
            continue
        out.append({
            "path": rel,
            "group": group,
            "title": title,
            "blurb": blurb,
            "kb": round(p.stat().st_size / 1024, 1),
        })
    return out


def write_site(skills_index: dict, libs_payload: dict) -> None:
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "assets").mkdir(exist_ok=True)

    skills_raw = load("skills.raw.json") or []
    skills_by_name = {s["name"]: s for s in skills_raw}

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": skills_index.get("stats", {}),
        "tree": skills_index.get("tree", {}),
        "docs": build_doc_manifest(),
        "skills": [
            {
                "name": s["name"],
                "slug": s["slug"],
                "description": s["description"],
                "domain": s["taxonomy"]["domain"],
                "subdomain": s["taxonomy"]["subdomain"],
                "capability": s["taxonomy"]["capability"],
                "path": s["path"],
                "h2": s["body"]["h2"],
                "code": s["body"]["code_blocks"],
                "links": len(s["body"]["external_links"]),
                "files": len(s["linked_files"]),
                "chars": s["body"]["chars"],
            }
            for s in skills_raw
        ],
        "libraries": libs_payload["libraries"],
    }
    (SITE / "assets" / "atlas.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )

    html = HTML_TEMPLATE.replace(
        "__PAYLOAD__", json.dumps(payload, ensure_ascii=False)
    ).replace("__GENERATED__", payload["generated_at"])
    html = html.replace("__DOMLAB__", json.dumps(DOMAIN_LABELS)).replace(
        "__CATLAB__", json.dumps(CATEGORY_LABELS)
    )
    html = html.replace("__DOCS__", json.dumps(payload["docs"], ensure_ascii=False))
    (SITE / "index.html").write_text(html, encoding="utf-8")
    print(f"site written : {SITE / 'index.html'}")


def write_docs(skills_index: dict, libs_payload: dict) -> None:
    skills_raw = load("skills.raw.json") or []
    by_domain: dict[str, list[dict]] = defaultdict(list)
    for s in skills_raw:
        by_domain[s["taxonomy"]["domain"]].append(s)

    # ---- spec compliance report -----------------------------------------
    sc = DOCS / "skills" / "spec-compliance.md"
    sc.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Skill spec compliance",
        "",
        "Checked against the Agent Skills spec. The portability boundary is narrow:",
        "only `name`, `description`, `license`, `compatibility`, `metadata` and",
        "`allowed-tools` survive a claude.ai upload or `package_skill.py`.",
        "Everything else is a local or Claude Code extension.",
        "",
        f"_{skills_index['stats']['spec_clean']} of {skills_index['stats']['total']} skills pass "
        "with no hard errors._",
        "",
        "| Code | Count | Meaning |",
        "|---|---|---|",
    ]
    MEANING = {
        "name-dir-mismatch": "`name:` in the frontmatter does not match the directory name — the spec expects them equal",
        "name-not-kebab-case": "`name:` is not lowercase-kebab-case",
        "name-too-long": "`name:` exceeds 64 characters",
        "missing-description": "no `description:` field",
        "missing-name": "no `name:` field",
        "description-too-long": "`description:` exceeds 1024 characters",
        "extension-fields-at-top-level": "Claude Code extension fields sit at the top level instead of under `metadata:`",
    }
    for code, n in sorted(skills_index["stats"].get("spec_issues", {}).items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{code}` | {n} | {MEANING.get(code, '—')} |")
    lines.append("")

    mismatches = [s for s in skills_raw if any(i["code"] == "name-dir-mismatch" for i in s["spec_compliance"]["issues"])]
    if mismatches:
        lines.append("## Name / directory mismatches")
        lines.append("")
        lines.append("| `name:` | directory | path |")
        lines.append("|---|---|---|")
        for s in mismatches:
            lines.append(f"| `{s['name']}` | `{s['dir']}` | `{s['relative_path']}` |")
        lines.append("")
    (sc).write_text("\n".join(lines), encoding="utf-8")

    for domain, skills in by_domain.items():
        d = DOCS / "skills"
        d.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# {DOMAIN_LABELS.get(domain, domain.title())}",
            "",
            f"_{len(skills)} skills in this domain._",
            "",
        ]
        sub_groups: dict[str, list[dict]] = defaultdict(list)
        for s in skills:
            sub_groups[s["taxonomy"]["subdomain"]].append(s)
        for sub in sorted(sub_groups):
            lines.append(f"## {sub}")
            lines.append("")
            for s in sorted(sub_groups[sub], key=lambda x: x["name"]):
                lines.append(f"### `{s['name']}`")
                lines.append("")
                if s["description"]:
                    lines.append(s["description"])
                    lines.append("")
                lines.append(
                    f"- **path**: `{s['path']}`\n"
                    f"- **code blocks**: {s['body']['code_blocks']} · "
                    f"**body**: {s['body']['chars']:,} chars · "
                    f"**linked files**: {len(s['linked_files'])}\n"
                    f"- **sections**: {', '.join(s['body']['h2'][:6]) or '—'}"
                )
                lines.append("")
        (d / f"{domain}.md").write_text("\n".join(lines), encoding="utf-8")

    # library catalog per category
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for l in libs_payload["libraries"]:
        by_cat[l.get("category") or "misc"].append(l)
    d = DOCS / "links"
    d.mkdir(parents=True, exist_ok=True)
    index = [
        "# Library catalog",
        "",
        f"_{len(libs_payload['libraries'])} entries, live-verified against npm + GitHub._",
        "",
        "| Category | Entries |",
        "|---|---|",
    ]
    for cat in sorted(by_cat):
        index.append(f"| [{CATEGORY_LABELS.get(cat, cat)}]({cat}.md) | {len(by_cat[cat])} |")
    (DOCS / "links" / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")

    for cat, items in by_cat.items():
        title = CATEGORY_LABELS.get(cat, cat.title())
        blurb = CATEGORY_BLURBS.get(cat, "")
        lines = [f"# {title} — links", ""]
        if blurb:
            lines += [blurb, ""]
        lines += [
            f"_{len(items)} entries. Stars and versions read live on {VERIFIED_ON}._",
            "",
        ]
        for l in sorted(items, key=lambda x: -(x.get("stars") or 0)):
            repo = l.get("repo")
            url = f"https://github.com/{repo}" if repo else (l.get("homepage") or "")
            label = f"[{l['name']}]({url})" if url else l["name"]
            desc = (l.get("description") or "").strip()
            if len(desc) > 150:
                desc = desc[:147].rsplit(" ", 1)[0] + "…"
            bits = []
            if l.get("npm"):
                bits.append(f"`{l['npm']}`")
            lic = (l.get("license") or "").strip()
            if lic and lic not in ("NOT FOUND", "None", "null"):
                if ":" in lic and len(lic) > 28:
                    lic = lic.split(":")[0].strip()
                bits.append(lic)
            if l.get("version"):
                bits.append(f"v{l['version']}")
            bits.append(f"{l['stars']:,}★" if l.get("stars") else "—★")
            lines.append(f"- **{label}** — {desc}  ")
            lines.append(f"  {' · '.join(bits)}")
        (d / f"{cat}.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"docs written : {DOCS}")


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>agent-atlas — animation, libraries, skills</title>
<style>
  :root {
    --bg: #0b0d10; --panel: #12151a; --panel2: #171b22; --line: #232a33;
    --fg: #e8edf4; --muted: #8b97a8; --accent: #6ee7b7; --accent2: #7dd3fc;
    --warn: #fbbf24; --bad: #f87171; --radius: 10px;
    --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--fg);
    font: 15px/1.55 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  }
  header {
    position: sticky; top: 0; z-index: 10;
    background: color-mix(in srgb, var(--bg) 88%, transparent);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--line); padding: 14px 22px;
    display: flex; gap: 18px; align-items: center; flex-wrap: wrap;
  }
  h1 { font-size: 17px; margin: 0; letter-spacing: -.2px; font-weight: 650; }
  h1 span { color: var(--accent); }
  .meta { color: var(--muted); font-size: 12.5px; font-family: var(--mono); }
  nav { display: flex; gap: 6px; margin-left: auto; }
  nav button {
    background: var(--panel2); border: 1px solid var(--line); color: var(--muted);
    padding: 6px 13px; border-radius: 7px; cursor: pointer; font-size: 13px;
    font-family: inherit; transition: .15s;
  }
  nav button:hover { color: var(--fg); border-color: #34404e; }
  nav button.on { background: var(--accent); color: #05231a; border-color: var(--accent); font-weight: 600; }
  main { padding: 22px; max-width: 1500px; margin: 0 auto; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 26px; }
  .card { background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); padding: 14px 16px; }
  .card b { display: block; font-size: 26px; font-weight: 680; letter-spacing: -.5px; }
  .card span { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .7px; }
  .controls { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }
  input[type=search], select {
    background: var(--panel); border: 1px solid var(--line); color: var(--fg);
    padding: 9px 13px; border-radius: 8px; font-family: inherit; font-size: 14px; min-width: 240px;
  }
  input[type=search]:focus, select:focus { outline: 1px solid var(--accent); border-color: var(--accent); }
  table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
  th {
    text-align: left; color: var(--muted); font-weight: 600; font-size: 11.5px;
    text-transform: uppercase; letter-spacing: .7px; padding: 9px 10px;
    border-bottom: 1px solid var(--line); position: sticky; top: 58px; background: var(--bg);
  }
  td { padding: 9px 10px; border-bottom: 1px solid #1a1f27; vertical-align: top; }
  tr:hover td { background: #131820; }
  a { color: var(--accent2); text-decoration: none; }
  a:hover { text-decoration: underline; }
  code, .mono { font-family: var(--mono); font-size: 12.5px; }
  .tag {
    display: inline-block; background: var(--panel2); border: 1px solid var(--line);
    color: var(--muted); padding: 1px 7px; border-radius: 20px; font-size: 11px; margin: 1px 3px 1px 0;
    font-family: var(--mono);
  }
  .tree { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; }
  .dom { background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); overflow: hidden; }
  .dom > h3 {
    margin: 0; padding: 11px 15px; font-size: 13.5px; background: var(--panel2);
    border-bottom: 1px solid var(--line); display: flex; justify-content: space-between;
  }
  .dom > h3 em { color: var(--muted); font-style: normal; font-size: 12px; font-family: var(--mono); }
  .sub { padding: 11px 15px; border-bottom: 1px solid #1a1f27; }
  .sub:last-child { border-bottom: none; }
  .sub h4 { margin: 0 0 7px; font-size: 12px; color: var(--accent); text-transform: uppercase; letter-spacing: .6px; }
  .sk { padding: 5px 0; }
  .sk b { font-size: 13.5px; }
  .sk p { margin: 1px 0 0; color: var(--muted); font-size: 12.3px; }
  .sk .m { color: #5f6b7d; font-size: 11px; font-family: var(--mono); }
  .err { color: var(--bad); font-size: 11px; font-family: var(--mono); }
  .warn { color: var(--warn); }
  .pill { font-size: 10.5px; padding: 1px 6px; border-radius: 4px; background: #2a2010; color: var(--warn); border: 1px solid #4a3a1a; }
  .hide { display: none; }
  #treeview { max-height: none; }
  .grid2 { display: grid; grid-template-columns: 340px 1fr; gap: 18px; align-items: start; }
  @media (max-width: 900px) { .grid2 { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<header>
  <h1>agent<span>·</span>atlas</h1>
  <div class="meta" id="hdr-meta"></div>
  <nav>
    <button data-v="overview" class="on">Overview</button>
    <button data-v="skills">Skill tree</button>
    <button data-v="libs">Libraries</button>
    <button data-v="docs">Docs</button>
  </nav>
</header>

<main>
  <section id="v-overview">
    <div class="cards" id="cards"></div>
    <div class="grid2">
      <div>
        <div class="controls">
          <input type="search" id="q" placeholder="search skills & libraries…" />
        </div>
        <div class="dom" style="margin-bottom:12px">
          <h3>Top domains <em id="top-domains"></em></h3>
          <div style="padding:12px 15px" id="domain-bars"></div>
        </div>
      </div>
      <div>
        <div class="dom">
          <h3>Most starred libraries <em>live from GitHub</em></h3>
          <div id="top-libs" style="padding:4px 0"></div>
        </div>
      </div>
    </div>
  </section>

  <section id="v-skills" class="hide">
    <div class="controls">
      <input type="search" id="q2" placeholder="filter skills…" />
      <select id="dom-filter"><option value="">all domains</option></select>
    </div>
    <div class="tree" id="skill-tree"></div>
  </section>

  <section id="v-libs" class="hide">
    <div class="controls">
      <input type="search" id="q3" placeholder="filter libraries…" />
      <select id="cat-filter"><option value="">all categories</option></select>
      <select id="sort-by">
        <option value="stars">sort: stars</option>
        <option value="dl">sort: downloads/wk</option>
        <option value="name">sort: name</option>
        <option value="pushed">sort: recently pushed</option>
      </select>
    </div>
    <table>
      <thead><tr>
        <th>Library</th><th>Package</th><th>Ver</th><th>Stars</th><th>DL/wk</th>
        <th>License</th><th>Size</th><th>Category</th>
      </tr></thead>
      <tbody id="lib-rows"></tbody>
    </table>
  </section>

  <section id="v-docs" class="hide">
    <div class="tree" id="doc-list"></div>
  </section>
</main>

<script>
const DATA = __PAYLOAD__;
const DOMLAB = __DOMLAB__;
const CATLAB = __CATLAB__;

const esc = s => (s ?? "").toString().replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fmt = n => n == null ? '—' : n >= 1e6 ? (n/1e6).toFixed(1)+'M' : n >= 1e3 ? (n/1e3).toFixed(1)+'k' : String(n);
const bytes = n => !n ? '—' : n >= 1048576 ? (n/1048576).toFixed(1)+' MB' : n >= 1024 ? (n/1024).toFixed(1)+' KB' : n+' B';

document.getElementById('hdr-meta').textContent =
  `${DATA.skills.length} skills · ${DATA.libraries.length} library entries · ${new Date(DATA.generated_at).toISOString().slice(0,16).replace('T',' ')}Z`;

// --- cards
const st = DATA.stats;
document.getElementById('cards').innerHTML = [
  ['Skills', st.total], ['Domains', st.domains], ['Code blocks', st.total_code_blocks],
  ['Linked files', st.total_linked_files], ['Body chars', st.total_body_chars], ['Libraries', DATA.libraries.length]
].map(([k,v]) => `<div class="card"><b>${typeof v === 'number' ? v.toLocaleString() : v}</b><span>${k}</span></div>`).join('');

// --- domain bars
const domCount = {};
DATA.skills.forEach(s => domCount[s.domain] = (domCount[s.domain]||0)+1);
const maxD = Math.max(...Object.values(domCount));
document.getElementById('domain-bars').innerHTML = Object.entries(domCount)
  .sort((a,b)=>b[1]-a[1])
  .map(([d,c]) => `<div style="display:flex;gap:9px;align-items:center;margin:5px 0">
      <span style="min-width:132px;font-size:12.5px">${DOMLAB[d]||d}</span>
      <span style="flex:1;height:7px;background:#1b212a;border-radius:4px;overflow:hidden">
        <span style="display:block;height:100%;width:${(c/maxD*100).toFixed(1)}%;background:linear-gradient(90deg,#6ee7b7,#7dd3fc)"></span></span>
      <span class="mono" style="min-width:30px;text-align:right;color:var(--muted)">${c}</span></div>`).join('');
document.getElementById('top-domains').textContent = Object.keys(domCount).length + ' total';

// --- top libs
const topL = [...DATA.libraries].filter(l=>l.stars).sort((a,b)=>b.stars-a.stars).slice(0,12);
document.getElementById('top-libs').innerHTML = topL.map(l =>
  `<div style="display:flex;gap:10px;align-items:center;padding:6px 15px;border-bottom:1px solid #1a1f27">
    <span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
      <a href="https://github.com/${esc(l.repo)}" target="_blank" rel="noopener">${esc(l.name)}</a>
      <span class="mono" style="color:#5f6b7d"> ${esc(l.npm||'')}</span></span>
    <span class="mono" style="color:var(--accent)">★${fmt(l.stars)}</span>
    <span class="mono" style="color:var(--muted);min-width:52px;text-align:right">${fmt(l.dl)}/wk</span>
  </div>`).join('');

// --- skill tree
const domSel = document.getElementById('dom-filter');
Object.keys(domCount).sort().forEach(d => domSel.insertAdjacentHTML('beforeend', `<option value="${d}">${DOMLAB[d]||d}</option>`));

function renderTree(filter='') {
  const f = filter.toLowerCase().trim();
  const groups = {};
  DATA.skills.forEach(s => {
    if (f) {
      const hay = [s.name, s.description, s.capability, s.subdomain, s.domain,
                   (s.h2 || []).join(' ')].join(' ').toLowerCase();
      if (!hay.includes(f)) return;
    }
    (groups[s.domain] ||= {}); (groups[s.domain][s.subdomain] ||= {})[s.capability] ||= [];
    groups[s.domain][s.subdomain][s.capability].push(s);
  });
  const doms = Object.entries(groups);
  document.getElementById('skill-tree').innerHTML = doms.length ? doms.map(([dom, subs]) => {
    const cnt = Object.values(subs).flatMap(c=>Object.values(c)).flat().length;
    const subHtml = Object.entries(subs).map(([sub, caps]) =>
      `<div class="sub"><h4>${esc(sub)}</h4>` + Object.entries(caps).map(([cap, list]) =>
        `<div style="margin-bottom:7px">${list.map(s =>
          `<div class="sk"><b>${esc(s.name)}</b>
            <span class="m">${s.code} code · ${s.files} files</span>
            <p>${esc((s.description||'').split('.')[0])}.</p></div>`).join('')}</div>`).join('') + `</div>`).join('');
    return `<div class="dom"><h3>${esc(DOMLAB[dom]||dom)}<em>${cnt} skills</em></h3>${subHtml}</div>`;
  }).join('') : `<p style="color:var(--muted)">no skills match "${esc(filter)}" — try a name like <code>animate</code>, <code>remotion</code>, or a domain like <code>creative</code></p>`;
}
renderTree();
document.getElementById('q2').addEventListener('input', e => renderTree(e.target.value));
domSel.addEventListener('change', e => renderTree(e.target.value));

// --- libraries
const catSel = document.getElementById('cat-filter');
const cats = [...new Set(DATA.libraries.map(l=>l.category).filter(Boolean))].sort();
cats.forEach(c => catSel.insertAdjacentHTML('beforeend', `<option value="${c}">${CATLAB[c]||c}</option>`));

function renderLibs() {
  const q = document.getElementById('q3').value.toLowerCase();
  const cat = catSel.value;
  const sort = document.getElementById('sort-by').value;
  let rows = DATA.libraries.filter(l => {
    if (cat && l.category !== cat) return false;
    if (!q) return true;
    return (l.name||'').toLowerCase().includes(q) || (l.npm||'').toLowerCase().includes(q)
        || (l.description||'').toLowerCase().includes(q) || (l.tags||[]).join(' ').toLowerCase().includes(q);
  });
  rows.sort((a,b) => sort==='name' ? (a.name||'').localeCompare(b.name||'')
    : sort==='dl' ? (b.dl||0)-(a.dl||0)
    : sort==='pushed' ? String(b.pushed||'').localeCompare(String(a.pushed||''))
    : (b.stars||0)-(a.stars||0));
  document.getElementById('lib-rows').innerHTML = rows.length ? rows.map(l => {
    const bad = (l.errors||[]).length;
    return `<tr>
      <td><a href="https://github.com/${esc(l.repo)}" target="_blank" rel="noopener">${esc(l.name)}</a>
        ${l.archived?'<span class="pill">archived</span>':''}
        ${bad?`<div class="err">${bad} unresolved field(s)</div>`:''}
        <div style="color:var(--muted);font-size:12px;max-width:430px">${esc((l.description||'').slice(0,110))}</div></td>
      <td class="mono">${esc(l.npm||'—')}</td>
      <td class="mono">${esc(l.version||'—')}</td>
      <td class="mono" style="color:var(--accent)">${fmt(l.stars)}</td>
      <td class="mono">${fmt(l.dl)}</td>
      <td class="mono">${esc(l.license||'—')}</td>
      <td class="mono">${bytes(l.unpacked)}</td>
      <td>${esc(CATLAB[l.category]||l.category||'—')}</td>
    </tr>`; }).join('') : `<tr><td colspan="8" style="color:var(--muted)">no libraries match</td></tr>`;
}
renderLibs();
['q3'].forEach(id => document.getElementById(id).addEventListener('input', renderLibs));
catSel.addEventListener('change', renderLibs);
document.getElementById('sort-by').addEventListener('change', renderLibs);

// --- docs
const DOCS = __DOCS__;
const byGroup = {};
DOCS.forEach(d => { (byGroup[d.group] ||= []).push(d); });
document.getElementById('doc-list').innerHTML = Object.entries(byGroup).map(([g, list]) =>
  `<div class="dom"><h3>${esc(g)}<em>${list.length} docs</em></h3>` +
  `<div style="padding:11px 15px">` + list.map(d =>
    `<div style="margin-bottom:11px"><a href="${esc(d.path)}" style="font-weight:600">${esc(d.title)}</a>
      <div class="m" style="color:var(--muted);font-size:12px;margin-top:2px">${esc(d.blurb)}</div>
      <div class="m" style="color:#5f6b7d;font-size:11px;font-family:var(--mono);margin-top:2px">${esc(d.path)} · ${d.kb} KB</div>
    </div>`).join('') + `</div></div>`).join('');

// --- nav
document.querySelectorAll('nav button').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('nav button').forEach(x => x.classList.remove('on'));
  b.classList.add('on');
  ['overview','skills','libs','docs'].forEach(v => document.getElementById('v-'+v).classList.toggle('hide', v !== b.dataset.v));
}));

// global search jumps to libs
document.getElementById('q').addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    document.getElementById('q3').value = document.getElementById('q').value;
    renderLibs();
    document.querySelector('nav button[data-v=libs]').click();
  }
});
</script>
</body>
</html>
"""


def main() -> None:
    skills_index = load("skills.index.json")
    libs = load("libs.live.json")
    if not skills_index or not libs:
        raise SystemExit("run extract_skills.py and scrape_libs.py first")

    payload = build_libs_payload(libs["libraries"])
    write_site(skills_index, payload)
    write_docs(skills_index, payload)


if __name__ == "__main__":
    main()
