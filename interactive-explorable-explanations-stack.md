# Interactive Explorable Explanations: Recommended Stack

## Context

Analysis of two approaches to interactive technical blog posts:
- **Distill.pub** (e.g., [Visual Exploration of Gaussian Processes](https://distill.pub/2019/visual-exploration-gaussian-processes/)) — Svelte 2 + D3 + SVG
- **Sophie Wang** (e.g., [JPEG compression](https://www.sophielwang.com/blog/jpeg)) — Next.js + React Three Fiber + Canvas 2D + hand-rolled rAF animations

Both produce interactive explorable explanations with in-browser math computation and real-time visualizations. They share the same educational philosophy (Bret Victor / Nicky Case lineage) but use fundamentally different rendering stacks.

---

## Distill's Approach (2019)

| Aspect | Details |
|---|---|
| **Framework** | Svelte 2 (`.html` component format, pre-Svelte 3) |
| **Rendering** | SVG exclusively — `<path>`, `<circle>`, `<ellipse>`, `<line>`, `<rect>` |
| **Animation** | D3 transitions — `d3.select(...).transition().duration(750).attr('d', ...)` |
| **Interaction** | D3 drag — `d3.drag().on('drag', ...)` for draggable handles, SVG `on:click` for toggling points |
| **Math** | ml-matrix (eigenvalue decomposition), custom GP sampling in JS |
| **Build** | Webpack + Babel, outputs to Distill's `<d-article>` Web Components template |
| **3D** | None — everything is 2D |
| **Easing** | D3's built-in easing (default ease for `.transition().duration(750)`) |
| **Data flow** | Svelte 2's `this.set()` / `this.get()` reactivity -> triggers D3 DOM updates in `onupdate()` |

**Strengths:** Accessible (screen readers can parse SVG), scales to any DPI, inspectable in devtools, prints cleanly, loads fast, works without a GPU, degrades gracefully. Easy for new contributors to understand. The ceiling is lower but the floor is higher.

**Philosophy:** SVG + D3 + Svelte is boring on purpose. It's a design discipline, not a limitation.

---

## Sophie Wang's Approach (2024)

| Aspect | Details |
|---|---|
| **Framework** | Next.js + MDX (React) |
| **Rendering** | WebGL via React Three Fiber (Three.js) for 3D particle systems + Canvas 2D (`getImageData`/`putImageData`) for pixel-level DSP visualizations |
| **Animation** | Hand-rolled `requestAnimationFrame` loops with custom smoothstep easing: `t*t*(3-2*t)` |
| **Interaction** | React `onChange` on `<input type="range">` sliders, React state (`useState`) drives re-renders |
| **Math** | Pure JS DCT, YCbCr color conversion, quantization, zigzag scan, Huffman encoding — all from scratch |
| **Build** | Next.js SSG with `next-mdx-remote` |
| **3D** | Heavy — point clouds of ~2000 particles with BufferGeometry, OrbitControls, perspective camera |
| **Easing** | Custom Hermite smoothstep + cubic ease-out, staggered per-parameter with manual delay offsets |
| **Data flow** | React state + `useMemo` for derived data, Three.js BufferAttribute mutations for GPU updates |

**Strengths:** The hero animation (particles morphing through RGB -> YCbCr -> channel separation -> DCT -> quantization -> compressed output) is genuinely stunning. 3D scatter plots with OrbitControls give spatial intuition that 2D projections can't. Real JPEG compression running in the browser with every intermediate step visualized.

**Costs:** WebGL excludes some users (old hardware, accessibility). ~900KB of JS (Three.js alone is huge). The 11-stage animation state machine with 20+ interpolation parameters is unmaintainable. The 3D hero is `display: none` on mobile (`hidden sm:block`).

### 9 Custom Interactive Components

1. **JpegPipelineHero** — 3D particle system (R3F), 11-stage rAF animation, smoothstep easing, ~2000 particles morphing between coordinate spaces
2. **InterpolatedColorSpacePlot** — R3F Canvas with `<points>` geometry, OrbitControls, cubic ease-out rAF morph between RGB and YCbCr, slice plane filtering
3. **DctBlockExplorer** — Canvas 2D, loads image -> extracts 8x8 blocks -> forward DCT in pure JS
4. **DctBasisAtlas** — Canvas 2D, generates all 64 DCT basis patterns (8x8 grid) with `Math.cos()`
5. **QuantizationExplorer** — Canvas 2D, adjustable quality slider, quantization table application
6. **JpegEntropyExplorer** — Canvas 2D, zigzag scan visualization (SVG polyline), Huffman/run-length encoding
7. **ChromaSubsamplingExplorer** — Image comparison with mouse hover for before/after (pre-rendered WebP images)
8. **ChromaSamplingGridExplorer** — Tailwind-styled div grids showing Y', Cb, Cr values per pixel
9. **ImageChannelExplorer** — Tab-based image swap with Tailwind transition classes

---

## Verdict

**Distill's philosophy is better for teaching.** Sophie's is better for wow. The GP post makes you understand Gaussian processes. The JPEG post makes you think "this is beautiful" and also teaches you JPEG — but a non-trivial chunk of the engineering serves the spectacle rather than the explanation. Sophie's Canvas 2D components (DCT, quantization) are arguably more pedagogically effective than her Three.js hero, and those are closer to Distill's approach.

The ideal is somewhere in between — Sophie's ambition with Distill's restraint. Use WebGL only when 3D genuinely aids understanding, keep everything else in SVG/Canvas 2D.

---

## Recommended Stack: Svelte 5 + SvelteKit + MDsveX

### Why Svelte

Svelte's reactivity model is tailor-made for interactive explanations. Compare updating a visualization parameter:

```js
// React — you fight the framework
const [quality, setQuality] = useState(70);
const dctCoeffs = useMemo(() => computeDCT(block, quality), [block, quality]);
useEffect(() => {
  const ctx = canvasRef.current.getContext('2d');
  drawCoeffs(ctx, dctCoeffs);  // manually sync to DOM
}, [dctCoeffs]);
```

```svelte
<!-- Svelte — you just write it -->
<script>
  let quality = $state(70);
  let dctCoeffs = $derived(computeDCT(block, quality));
</script>
<canvas use:bindCanvas={dctCoeffs} />
```

No `useMemo` dependency arrays to get wrong. No stale closures. No `useRef` dance for canvas. Svelte compiles reactivity away — there's no virtual DOM diffing thousands of SVG nodes on every slider tick.

### The Full Stack

| Layer | Choice | Why |
|---|---|---|
| **Content** | MDsveX | Markdown with Svelte components inline. Same idea as MDX but less friction |
| **2D plots** | SVG + D3 (scales/shapes only) | Use D3 for `d3.scaleLinear`, `d3.line`, `d3.area` — the math parts. Let Svelte own the DOM. Never use `d3.select().append()` |
| **Pixel work** | Canvas 2D | `getImageData`/`putImageData` for DSP-type visualizations. Svelte `use:` actions bind nicely to canvas |
| **3D (when needed)** | Threlte | Svelte's Three.js wrapper. Declarative scene graph like R3F but with Svelte's reactivity, which plays much better with Three's imperative internals |
| **Animation** | Svelte `tweened` + `spring` | Built-in, reactive, tiny. `let progress = tweened(0); progress.set(1)` — done. No library needed |
| **Complex choreography** | Motion One (`motion` package) | Lightweight (~3KB), modern, timeline API for staggered multi-stage sequences. Unlike GSAP: MIT licensed, tree-shakeable |
| **Deploy** | SvelteKit static adapter | Pre-renders everything. Zero JS for prose, hydrates only interactive islands |

### Key Design Principle

**SVG should be your default.** It's accessible, it prints, it scales, it's inspectable. Only escape to Canvas when you're doing pixel math. Only escape to WebGL when 3D genuinely teaches something a 2D view can't.

### What This Gets You Over Both Approaches

**vs Distill (Svelte 2 + D3 DOM manipulation):**
- Svelte 5's `$state`/`$derived` replaces the `set()`/`get()`/`onupdate()` boilerplate
- No more D3 fighting with Svelte for DOM ownership — D3 computes, Svelte renders
- `tweened`/`spring` replace `d3.transition()` with something reactive instead of imperative
- SvelteKit's static adapter gives better performance than Distill's custom Web Components build

**vs Sophie (React + R3F + hand-rolled everything):**
- No `useEffect`/`useMemo`/`useRef` ceremony — Svelte's reactivity just works
- `tweened(0)` replaces her entire hand-rolled rAF + smoothstep state machine
- Threlte gives the same Three.js power as R3F with less boilerplate
- Compiled output is ~40% smaller than React equivalent — matters when shipping 9 interactive components on one page
- Svelte transitions (`in:fade`, `in:fly`) handle the UI chrome animations that Sophie is using Tailwind `transition-*` classes for

### Conceptual Example: Sophie's 11-Stage Hero in Svelte

```svelte
<script>
  import { tweened } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';

  const stages = ['image','rgb','ycbcr','channels','subsample',
                  'patch','dct','quant','reconstruct','entropy','jpeg'];
  let stageIndex = $state(0);
  let progress = tweened(0, { duration: 1800, easing: cubicOut });

  // each visual parameter is just a derived reactive value
  let rgbFade = $derived(
    stageIndex >= 1 ? 1
    : $progress > 0.16 ? smoothstep(($progress - 0.16) / 0.26)
    : 0
  );
  let ycbcrFade = $derived(
    stageIndex >= 2 ? 1
    : stageIndex === 1 ? smoothstep(($progress - 0.04) / 0.2)
    : 0
  );
  // ... same math, but reactive instead of imperative
</script>

<Canvas>
  <Points positions={interpolatedPositions} colors={interpolatedColors} />
</Canvas>
```

No rAF loop. No manual cleanup. No `cancelAnimationFrame`. Svelte handles it.

---

## References

- [Distill.pub GP post source](https://github.com/distillpub/post--visual-exploration-gaussian-processes)
- [Sophie Wang's JPEG post](https://www.sophielwang.com/blog/jpeg)
- [Threlte (Svelte + Three.js)](https://threlte.xyz/)
- [MDsveX](https://mdsvex.pngwn.io/)
- [Motion One](https://motion.dev/)
- [Svelte 5 reactivity docs](https://svelte.dev/docs/svelte/$state)
