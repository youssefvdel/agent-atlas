# Documentation index

Everything here was **scraped and verified live** on 2026-10-20. No star count,
version, license, or install count in these documents came from memory.

---

## Pick a tool before you start

| Document | What it answers |
|---|---|
| [**start-here.md**](start-here.md) | **The 2026 stack in one page** — what to install, what is hype, what is real, the 10 repos worth reading the source of |
| [**claude-code-tooling.md**](ecosystem/claude-code-tooling.md) | The 5-minute baseline setup, the decision table, and the pitfalls. Read this one first if you are about to start a project |
| [**before-you-start.md**](libraries/before-you-start.md) | Which library for which job — CSS-first routing tables, anti-patterns |
| [**design-skills.md**](ecosystem/design-skills.md) | Which AI design skills are real, and the `SKILL.md` vs component-code distinction |

## Libraries

| Document | What it answers |
|---|---|
| [**animation-libraries.md**](libraries/animation-libraries.md) | 50 libraries, deep-dive, with real API signatures read from the shipped `.d.ts` files |
| [**modern-css.md**](libraries/modern-css.md) | What CSS can do natively in 2026 — verified against MDN browser-compat-data |
| [**code-video.md**](libraries/code-video.md) | Making video from code — 41 tools, 22 experiments actually run on this machine |
| [**creative-libs.md**](libraries/creative-libs.md) | 67 "hairline class" repos with live stars and install commands |
| [**ux-craft-2026.md**](libraries/ux-craft-2026.md) | The high-craft web repos of 2026, tiered by craft |
| [**anchor-hairline.md**](libraries/anchor-hairline.md) | The reference repo, fully documented |
| [**hairline-design-study.md**](libraries/hairline-design-study.md) | The ten rules for pointer-reactive interface figures |

## The skill ecosystem

| Document | What it answers |
|---|---|
| [**agent-skills-ecosystem.md**](ecosystem/agent-skills-ecosystem.md) | How the spec works, client conventions, MCP registries, verified ecosystem repos |
| [**design-skills.md**](ecosystem/design-skills.md) | The AI-design skill tier, ranked by installs (not stars — see below) |
| [**youtube-design.md**](ecosystem/youtube-design.md) | 80 verified videos, with the concrete techniques each one teaches |
| [**tiktok-hyped.md**](ecosystem/tiktok-hyped.md) | What is actually being hyped, and which claims are substance |

## This machine's skills

| Document | What it answers |
|---|---|
| **[../data/skills.tree.md](../data/skills.tree.md)** | The rendered hierarchy of all 110 installed skills |
| **[spec-compliance.md](skills/spec-compliance.md)** | Which skills violate the spec, and which fields are portable |
| `skills/engineering.md`, `skills/creative.md`, … | Per-domain breakdowns with section lists and code-block counts |

---

## Three findings worth knowing before you read anything else

**1. Stars and installs disagree, and installs are the better signal.**
`designed-by-ai/skills` has 19 stars and 916,408 installs — but its README
tells you to run `npx skills add sleekdotdesign/agent-skills`, so those installs
belong to a *different* repo. Install counters are attributable and resellable;
star counts are not. Rank by installs and shipped `SKILL.md` files.

**2. The `skills` CLI is not Anthropic's.**
`npx skills add <owner>/<repo>` is [vercel-labs/skills](https://github.com/vercel-labs/skills)
(MIT, 35.8k stars, 22.9M downloads/month). Anthropic publishes *skills*; the CLI
is harness-agnostic and installs into 75+ agents.

**3. GSAP is entirely free now.**
Since 3.13 (2025-04-29) every plugin — SplitText, MorphSVG, DrawSVG,
ScrollSmoother, InertiaPlugin — is free for commercial use. Club GSAP wound
down. Advice that says otherwise is out of date.

---

## The numbers

| | |
|---|---|
| Skills indexed | **110** across 7 domains, 12 subdomains, 0 unclassified |
| Code blocks in those skills | **1,028** |
| Linked files (references/, scripts/, assets/) | **313** |
| Libraries catalogued | **249** (88 npm-backed + 161 GitHub-only) |
| npm packages resolved to a canonical repo | **88 / 88**, 0 unresolved |
| Research documents | **9**, ~450 KB |
