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
| **Get the whole 2026 stack in one page** | [`docs/start-here.md`](docs/start-here.md) — what to install, what is hype, what is real |
| Know what to install before starting a project | [`docs/ecosystem/claude-code-tooling.md`](docs/ecosystem/claude-code-tooling.md) — the 5-minute baseline, the decision table, the pitfalls |
| Pick an animation / CSS / video library | [`docs/libraries/before-you-start.md`](docs/libraries/before-you-start.md) |
| Know what CSS can do natively in 2026 | [`docs/libraries/modern-css.md`](docs/libraries/modern-css.md) |
| Get real APIs for every animation library | [`docs/libraries/animation-libraries.md`](docs/libraries/animation-libraries.md) |
| Make video from code | [`docs/libraries/code-video.md`](docs/libraries/code-video.md) |
| Find AI design skills that actually work | [`docs/ecosystem/design-skills.md`](docs/ecosystem/design-skills.md) |
| Browse the hype repos | [`docs/libraries/creative-libs.md`](docs/libraries/creative-libs.md) · [`docs/ecosystem/tiktok-hyped.md`](docs/ecosystem/tiktok-hyped.md) |
| Learn the craft behind `hairline` | [`docs/libraries/hairline-design-study.md`](docs/libraries/hairline-design-study.md) |
| Understand how agent skills work | [`docs/ecosystem/agent-skills-ecosystem.md`](docs/ecosystem/agent-skills-ecosystem.md) |
| Browse the skill tree | [`data/skills.tree.md`](data/skills.tree.md) |

Full index: [`docs/README.md`](docs/README.md)

The repo is also an installable agent skill — `SKILL.md` in the root is a
routing layer over all of the above. Copy it to `~/.hermes/skills/agent-atlas/`
and the atlas becomes queryable by the agent itself.

## Five findings that change the advice

**1. Stars lie, installs don't.**
`designed-by-ai/skills` has 19 stars and 916,408 installs — but its README
points you at a *different* repo. Install counters are attributable; star
counts are not. Rank by installs and shipped `SKILL.md` files.

**2. The `skills` CLI is not Anthropic's.**
`npx skills add <owner>/<repo>` is [vercel-labs/skills](https://github.com/vercel-labs/skills)
(MIT, 35.8k stars, 22.9M downloads/month). Anthropic publishes *skills*; that
CLI is harness-agnostic and installs into 75+ agents.

**3. GSAP is entirely free now.**
Since 3.13 (2025-04-29) every plugin — SplitText, MorphSVG, DrawSVG,
ScrollSmoother, InertiaPlugin — is free for commercial use. Club GSAP wound
down. Advice saying otherwise is out of date.

**4. A repo with 80k stars is not automatically a skill.**
`DavidHDev/react-bits` (49.8k stars) ships **zero** `SKILL.md` files — its
`skill-*.webp` files are marketing images. Check with:
```sh
gh api repos/<owner>/<repo>/git/trees/HEAD?recursive=1 \
  --jq '[.tree[].path | select(test("SKILL.md$"))] | length'
```

**5. `AGENTS.md` silently stops loading.**
Claude Code v2.1.277+ reads `AGENTS.md` natively — but only if no
`CLAUDE.md`/`CLAUDE.local.md` exists anywhere above it.

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
