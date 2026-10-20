# Before you start: which tool to reach for

> A decision guide, not a library list. The libraries are catalogued elsewhere;
> this is the *selection* layer.
>
> Everything here is grounded in the live-verified data in `data/libs.live.json`
> and the research documents in this folder.

---

## The one decision that matters most

**Do you need a JS animation engine at all?**

Modern CSS (2024–2026) covers more than most people reach for GSAP to do. Check
`docs/libraries/modern-css.md` before pulling in a library:

| If you need… | Use this, not a library |
|---|---|
| Scroll-linked reveals, parallax | `animation-timeline: view()` + `animation-range` |
| Page/modal transitions | View Transitions API (`@view-transition`, `startViewTransition`) |
| Entry animations for elements that didn't exist | `@starting-style` + `transition-behavior: allow-discrete` |
| Animating a custom property | `@property` (registered custom properties) |
| Component-aware layouts | `@container` + container query units |
| Tabular figures / resting states | `color-mix()`, `oklch()`, `light-dark()` |

**Rule of thumb:** if it's a one-off transition, CSS. If it's a timeline with
sequencing and interruption, a library.

---

## Animation engine

| Reach for | When | Why not the other one |
|---|---|---|
| **GSAP** | Complex timelines, scroll choreography, production marketing sites | Free tier excludes Club plugins; heavy for simple fades |
| **Motion** (`motion.dev`) | React components, layout animation, `layoutId` shared-element transitions | Less powerful for long scroll timelines than GSAP ScrollTrigger |
| **anime.js v4** | Vanilla JS, timeline control, tiny footprint, ESM-first | Weaker ecosystem; no React binding |
| **react-spring** | React + physics, gesture-driven values | More boilerplate than Motion for layout work |
| **CSS only** | Simple fades, transforms, one-off states | No interruption handling, no sequencing |

**GSAP 3.13+ made every Club plugin free** (SplitText, MorphSVG, DrawSVG,
ScrollSmoother, InertiaPlugin). If you were told those are paid, that advice is
out of date — see `docs/libraries/animation-libraries.md`.

**The two-clock rule** (from the hairline study, and it applies everywhere):

- **Discrete** change (which item is selected) → long ease-out, ~700ms on
  `(.32, .72, 0, 1)`
- **Continuous** input (where the pointer is) → **spring**, not a timed ease,
  because the target moves every frame and a timed ease is always chasing it

Mixing these up is the most common production animation bug.

---

## Scroll

| Reach for | When |
|---|---|
| **Lenis** | Smooth scrolling that still respects native scroll (GSAP ScrollTrigger integrates cleanly) |
| **Locomotive Scroll v5** | Heavier virtual-scroll feel; rebuilt on top of Lenis |
| **CSS scroll-driven** | Reveals and parallax with zero JS — best for static content pages |
| **GSAP ScrollTrigger** | Pinned sections, scrubbed timelines, snap points |

> **Don't** use `smooth-scrollbar` (unmaintained since 2023) or
> `ScrollReveal` (GPL-3.0, unmaintained since 2021) for new work. Lenis
> replaced both.

---

## Carousel / drawer / gesture

| Reach for | When |
|---|---|
| **Embla** | Accessible, 6.9 kB, best-in-class swipe physics |
| **Swiper** | Feature-rich, huge plugin ecosystem, but 20 kB+ |
| **Vaul** | Bottom drawer with gesture-to-dismiss (React) |
| **use-gesture** | Raw pointer/drag/pinch primitives |
| **Auto-Animate** | List reorder animation in ~1 kB, framework-agnostic |

---

## Vector / animation runtime

| Reach for | When |
|---|---|
| **Lottie** (`lottie-web`, `lottie-react`) | Designer-exported JSON animations; the de-facto standard |
| **dotLottie** | Same content, WASM-compiled, themeable, smaller |
| **Rive** | Interactive, state-machine-driven — animations that *respond* to input, not just play |
| **SVG.js / Two.js** | Programmatic SVG drawing/manipulation |

---

## Code → video

| Reach for | When |
|---|---|
| **Remotion** | React components → MP4. The industry default. License: free for individuals/small companies, paid for larger orgs |
| **Revideo** (`@revideo/core`) | Open-source Remotion fork, MIT |
| **Motion Canvas** | TypeScript scripted animation, Paper.js-based, great for math/data visuals |
| **Manim Community** | Python + LaTeX → animation. Unbeatable for mathematical explainers |
| **WebCodecs + mp4box.js** | Low-level, in-browser encode + mux, full control over timing |
| **Playwright / Puppeteer** | Deterministic frame capture from a live page (see determinism notes below) |

**Determinism matters more than people expect.** To make browser capture
frame-accurate:

1. Freeze the clock — drive time explicitly instead of using `Date.now()`
2. Seed the RNG — no `Math.random()` in render paths
3. Load fonts deterministically — `document.fonts.ready` before capture
4. Use `--virtual-time-budget` (Chromium) or a fixed-step ticker
5. Capture the **canvas**, not the DOM, when the output is a video

---

## The hairline class — for delight, not utility

If the goal is *"this makes people stop and look"* rather than *"this works"*:

- **[@lucasmarkes/hairline](https://github.com/lucasmarkes/hairline)** — 33
  isometric line figures that answer the pointer. Zero dependencies, MIT.
  The `intensity` slider design is worth stealing: it makes the interaction
  design space *legible*.
- **[magicuidesign/magicui](https://github.com/magicuidesign/magicui)** — animated
  component library, copy-paste, MIT
- **[DavidHDev/react-bits](https://github.com/DavidHDev/react-bits)** — the
  largest open-source library of animated React/Next components
- **[ibelick/motion-primitives](https://github.com/ibelick/motion-primitives)** —
  animated UI kit, MIT
- **[nolly-studio/cult-ui](https://github.com/nolly-studio/cult-ui)** — 150+ free
  shadcn/ui components built with Tailwind + Motion

See `creative-libs.md` for 67 more.

---

## Anti-patterns

| Don't | Why |
|---|---|
| Reach for a library before checking if CSS does it | A 27 kB dependency for a fade is a real cost |
| Use GSAP Club plugins believing they're paid | Free since 3.13 |
| Pick a library by star count alone | `smooth-scrollbar` has 3.3k stars and hasn't been touched since 2023 |
| Animate `width`/`height`/`top`/`left` | Layout thrash — animate `transform` and `opacity` |
| Use one clock for both discrete and continuous | See the two-clock rule above |
| Forget `prefers-reduced-motion` | It's an accessibility requirement, not a nice-to-have |
| Copy a skill repo without reading its SKILL.md | "Installs with npx" ≠ "understands your codebase" |
