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

## Where to look

| Question | File |
|---|---|
| Which library, and what are its real APIs? | `docs/libraries/animation-libraries.md` |
| What can CSS do natively in 2026? | `docs/libraries/modern-css.md` |
| How do I make video from code? | `docs/libraries/code-video.md` |
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
