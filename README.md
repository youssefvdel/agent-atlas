# agent-atlas

A living knowledge base for **web animation, code-to-video, creative front-end libraries, and the agent-skill ecosystem** — everything scraped and verified live, then organised as a hierarchy you can actually navigate.

Built by an agent, for agents. Every number in here came from a live API response; nothing is remembered from training data.

---

## What's in it

| Part | What it is | Live count |
|---|---|---|
| `docs/skills/` | Every agent skill installed on this machine, parsed and filed into a taxonomy | **107 skills** |
| `docs/libraries/` | Animation / creative / video libraries, each verified against npm + GitHub | **143 targets → verified** |
| `docs/ecosystem/` | The wider agent-skill ecosystem, MCP registries, and how the specs actually work | ecosystem research |
| `data/` | Machine-readable JSON + YAML indexes (the source of truth) | `skills.index.json`, `libs.live.json` |
| `tools/` | The scrapers and extractors that regenerate everything | 5 scripts |
| `site/` | An interactive browser for the whole atlas | `index.html` |

## Read this first

| If you want to… | Open |
|---|---|
| Pick a library before starting a project | [`docs/libraries/before-you-start.md`](docs/libraries/before-you-start.md) |
| Know what CSS can do natively in 2026 | [`docs/libraries/modern-css.md`](docs/libraries/modern-css.md) |
| Get real APIs for every animation library | [`docs/libraries/animation-libraries.md`](docs/libraries/animation-libraries.md) |
| Make video from code | [`docs/libraries/code-video.md`](docs/libraries/code-video.md) |
| Browse the hype repos | [`docs/libraries/creative-libs.md`](docs/libraries/creative-libs.md) |
| Read the craft rules behind `hairline` | [`docs/libraries/hairline-design-study.md`](docs/libraries/hairline-design-study.md) |
| Understand how agent skills work | [`docs/ecosystem/agent-skills-ecosystem.md`](docs/ecosystem/agent-skills-ecosystem.md) |
| Browse the skill tree | [`data/skills.tree.md`](data/skills.tree.md) |

The repo is also an installable agent skill — `SKILL.md` in the root is a
routing layer over all of the above. Copy it to `~/.hermes/skills/agent-atlas/`
and the atlas becomes queryable by the agent itself.

## The pipeline

```
~/.hermes/skills/**/SKILL.md
        │
        ├── tools/extract_skills.py ──────► data/skills.raw.json
        │                                     data/skills.index.json
        │                                     data/skills.tree.md
        │
data/libs.spec.json  (hand-written target list)
        │
        ├── tools/resolve_spec.py ────────► data/libs.spec.resolved.json   (fix broken npm names / repos)
        ├── tools/canonicalize_spec.py ───► data/libs.spec.canonical.json  (npm's own repository field)
        ├── tools/resolve_repos.py ───────► data/libs.spec.final.json      (verify via repo package.json)
        │
        └── tools/scrape_libs.py ─────────► data/libs.live.json            (npm + GitHub + downloads)
```

## Why it exists

The ecosystem moves weekly. `anime.js` v4 landed, GSAP 3.13 made every Club plugin free, `@revideo/core` replaced `@revideo/2.0`, orgs rename repos so hard links 404. A hand-written list goes stale in weeks.

So the list is **generated**, not written. The spec file holds *targets*; the scraper resolves *truth*.

## The hairline case

`lucasmarkes/hairline` — 33 isometric line figures that answer the pointer, 2.4k stars, MIT, zero dependencies, a React binding that's an optional peer. The kind of repo that makes you want to know what else is in that class. That's what the `docs/libraries/creative-libs.md` and `docs/ecosystem/` documents are for.

## Regenerating

```sh
cd ~/Projects/agent-atlas

# skills (parses ~/.hermes/skills)
python3 tools/extract_skills.py --out data/

# libraries (needs network; GITHUB_TOKEN recommended)
export GITHUB_TOKEN=$(gh auth token)
python3 tools/resolve_repos.py  --spec data/libs.spec.json --out data/libs.spec.final.json
python3 tools/scrape_libs.py    --spec data/libs.spec.final.json --out data/libs.live.json

# rebuild the site
python3 tools/build_site.py
```

## Rules this repo follows

1. **No invented numbers.** Stars, versions, licences and download counts come from live API responses. A field that could not be resolved is recorded as an error, not a guess.
2. **Verified repo resolution.** A GitHub repo is only accepted when the repo's own `package.json` `name` matches the npm package. Search-by-description is a trap — it hands you `rustdesk` for `remotion`.
3. **Forks are never the canonical source.** npm's `repository` field sometimes points at a personal fork; the resolver prefers the highest-starred non-fork, non-archived match.
4. **Errors are recorded, not hidden.** `data/libs.live.json` keeps an `errors` array per entry.

## Layout

```
agent-atlas/
├── README.md
├── data/
│   ├── skills.raw.json         every skill, full metadata
│   ├── skills.index.json       taxonomy + tree + stats
│   ├── skills.index.yaml       same, YAML
│   ├── skills.tree.md          rendered tree
│   ├── libs.spec.json          hand-written target list
│   ├── libs.spec.final.json    resolved + verified
│   ├── libs.live.json          live npm + GitHub data
│   └── libs.resolve-report.json
├── docs/
│   ├── skills/                 per-domain skill documentation
│   ├── libraries/              per-category library catalogs
│   └── ecosystem/              agent-skill ecosystem research
├── tools/                      the pipeline
└── site/                       interactive browser
```

## License

Research and tooling: MIT. Catalogued library code and documentation remain under their own licenses — each entry in `data/libs.live.json` records the authoritative license.
