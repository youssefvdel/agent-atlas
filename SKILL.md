---
name: agent-atlas
description: Use when choosing an animation library, CSS technique, video-generation tool, or agent skill for a front-end project — or when asked what tool to reach for before starting. Covers GSAP vs Motion vs anime.js, modern CSS (View Transitions, scroll-driven, @starting-style), Lottie/Rive, Remotion/code-to-video, and the Claude Code skill ecosystem, with live-verified versions, stars, licenses, and decision guides. Triggers on "which animation library", "best library for", "before I start building", "design skills for Claude Code", "agent skills for frontend".
---

# agent-atlas

A live-verified knowledge base for front-end craft. The full catalog lives at
`~/Projects/agent-atlas`; this skill is the routing layer.

## Use this skill when

- Picking an animation / scroll / carousel / vector-animation library
- Deciding whether a technique is CSS-only or needs JS
- Choosing a code-to-video tool (Remotion / Revideo / Manim / WebCodecs)
- Looking for a Claude Code / agent skill that does design or front-end work
- Answering "what should I use to build X" for a web UI

## The short version

**Check CSS first.** Modern CSS (2024–2026) covers most transitions, reveals,
and page transitions without a dependency:

| Need | Technique |
|---|---|
| Scroll reveal / parallax | `animation-timeline: view()` + `animation-range` |
| Page & modal transition | View Transitions API (`@view-transition`, `startViewTransition`) |
| Entry animation for new elements | `@starting-style` + `transition-behavior: allow-discrete` |
| Animatable custom property | `@property` |
| Component-aware layout | `@container` + `cqi`/`cqw` units |

Only reach for JS when you need **sequencing**, **interruption handling**, or
**scrubbed scroll timelines**.

## Library routing

| Need | Reach for |
|---|---|
| Complex timelines, scroll choreography | **GSAP** (all Club plugins free since 3.13) |
| React layout animation, shared-element | **Motion** (`motion.dev`) |
| Vanilla timeline control, tiny | **anime.js v4** |
| React + physics | **react-spring** |
| Smooth scroll | **Lenis** (not `smooth-scrollbar` — dead since 2023) |
| Accessible carousel | **Embla** |
| Bottom drawer, gesture dismiss | **Vaul** |
| Designer-exported vector animation | **Lottie** / **dotLottie** |
| Interactive, state-machine animation | **Rive** |
| React → MP4 | **Remotion** (or **Revideo** for MIT) |
| Math / LaTeX animation | **Manim Community** |
| Low-level in-browser encode | **WebCodecs** + `mp4box.js` |

## The two-clock rule

Applies to every animation you write:

- **Discrete** change (which item is active) → long ease-out, ~700ms on
  `(.32, .72, 0, 1)`
- **Continuous** input (pointer position) → **spring**, never a timed ease —
  the target moves every frame and a timed ease is always chasing it

Mixing them is the most common production animation bug.

## The hairline study

`lucasmarkes/hairline` (MIT, zero deps) documents ten rules for pointer-reactive
interface figures. The most transferable:

1. **Hit areas don't move** — test the pointer against the rest or target
   pose, never the current pose, or you get a flicker loop
2. **Stagger by distance** — `delay = |i − a| × step`, 30–60ms
3. **Clamp the reach** — the figure must stay composed at the slider's far end
4. **The stroke is the only highlight** — colour means information
5. **Rest is designed, never flat** — the still frame is the thumbnail
6. **Two clocks** — see above
7. **No words inside the figure** — geometry carries identity

Full text: `docs/libraries/hairline-design-study.md`

## Three corrections that change the advice

**1. The `skills` CLI is not Anthropic's.**
`npx skills add <owner>/<repo>` is **vercel-labs/skills** (MIT, 35.8k stars,
22.9M downloads/month). Anthropic publishes *skills*; that CLI is
harness-agnostic and installs into 75+ agents. Official Anthropic skills are
installed via the plugin marketplace: `/plugin marketplace add anthropics/skills`.

**2. Stars lie, installs don't.**
`designed-by-ai/skills` has 19 stars and 916,408 installs — but its README
points at a *different* repo, so those installs belong to
`sleekdotdesign/agent-skills` (589 stars). Install counters are attributable
and resellable; star counts are not. Rank by installs and shipped `SKILL.md`
files.

**3. GSAP is entirely free now.**
Since 3.13 (2025-04-29) every plugin — SplitText, MorphSVG, DrawSVG,
ScrollSmoother, InertiaPlugin — is free for commercial use. Club GSAP wound
down and the private npm was retired. Advice that says those are paid is out
of date.

## The two skills that matter most

**`frontend-design`** (Anthropic, `anthropics/skills`) — 1,007,521 installs.
A plain markdown file. Its body explicitly bans "Roboto, Inter, Arial… purple
gradients on white backgrounds". A 6-agent bake-off found Opus 4.5 *worst* on
raw output but *best* with the skill loaded — **the skill supplies taste, not
the model**.

**`web-design-guidelines`** (Vercel, `vercel-labs/agent-skills`) — 760,123
installs. A linter for your own UI.

**`taste-skill`** (`Leonxlnx/taste-skill`) — 640,624 installs.

## The SKILL.md vs component-code distinction

A repo with 80k stars is not automatically a skill. Verified by walking git
trees:

**Zero `SKILL.md` — component code only:**
`ibelick/motion-primitives` · `DavidHDev/react-bits` (its `skill-*.webp` files
are marketing images) · `Trystan-SA/claude-design-system-prompt` (plain `.md`
prompt library) · `wilwaldon/Claude-Code-Frontend-Design-Toolkit` (README
pointer) · `figma/community-resources` (index) · `shadcn-ui/lint` (npm linter) ·
`iart-ai/motion-skills` (hub README claiming "50 skills" that live in 18
sibling repos)

**Real skills:** `nexu-io/open-design` (549) · `educlopez/ui-craft` (217) ·
`wshobson/agents` (185) · `Owl-Listener/designer-skills` (111) ·
`figma/mcp-server-guide` (32) · `plugin87/ux-ui-agent-skills` (27) ·
`pbakaus/impeccable` (25 — but only **2 unique** skills vendored into 19
harness folders)

**Third format:** `DESIGN.md` as a separate channel.

## Two traps in the ecosystem

**`AGENTS.md` silently stops loading.**
Claude Code v2.1.277+ reads `AGENTS.md` natively — but **only if there is no
`CLAUDE.md` or `CLAUDE.local.md` anywhere above it**. Adding a
`CLAUDE.local.md` kills `AGENTS.md` loading with no error.

**The methodology layer conflicts with itself.**
ECC's own manifest says *"YOU MUST UNINSTALL OTHER VERSIONS OF SUPERPOWERS"*.
Superpowers / ECC / gstack / mattpocock / addyosmani are genuinely competing.
Same for 4 competing memory layers and 5 browser layers. Pick one.

## Where to look

| Question | File |
|---|---|
| What do I install before starting a project? | `docs/ecosystem/claude-code-tooling.md` |
| Which library, and what are its real APIs? | `docs/libraries/animation-libraries.md` |
| What can CSS do natively in 2026? | `docs/libraries/modern-css.md` |
| How do I make video from code? | `docs/libraries/code-video.md` |
| Which AI design skills are real? | `docs/ecosystem/design-skills.md` |
| What are the hype repos? | `docs/libraries/creative-libs.md` |
| What do I reach for before starting? | `docs/libraries/before-you-start.md` |
| How do agent skills work? | `docs/ecosystem/agent-skills-ecosystem.md` |
| What skills are on this machine? | `data/skills.tree.md` |
| Live stars/versions/licenses | `data/libs.live.json` |

## Regenerating the data

```sh
cd ~/Projects/agent-atlas
export GITHUB_TOKEN=$(gh auth token)
python3 tools/extract_skills.py --out data/                       # local skills
python3 tools/resolve_repos.py --spec data/libs.spec.json \
        --out data/libs.spec.final.json                            # verify repos
python3 tools/scrape_libs.py --spec data/libs.spec.final.json \
        --out data/libs.live.json                                 # live npm+GitHub
python3 tools/build_site.py                                        # site + docs
```

The site is `site/index.html` (open it directly, or serve the folder).

## Rules

1. **Never quote a star count or version from memory** — read
   `data/libs.live.json` or hit the API.
2. **A repo is only canonical if it is non-fork, non-archived, and the package
   name matches.** npm's `repository` field usually wins, but it sometimes
   points at an impersonator (`dmiller9911/react-bits`, 5★, vs the real
   49k★ one) — the resolver checks stars for that reason.
3. **Before recommending a library, check the CSS table above.** Shipping a
   27 kB dependency for a fade is a real cost.
4. **Every recommendation must include its license and maintenance status.**
   `smooth-scrollbar` has 3.3k stars and is abandoned; `ScrollReveal` is
   GPL-3.0 and dead since 2021.
