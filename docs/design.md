# RAG Document Q&A: Design Specification
Version 1.0 · Status: Draft · Scope: Chat, Library, Eval Dashboard (Settings, auth, admin = out of scope) · Method: design-intelligence skill, spec-only mode (no code modified; no external sites inspected)

> **AI AGENT RULE (memory):** Read `memory.md` before UI work; after UI changes log decisions/deviations there and update this file. Create `memory.md` if missing. Use tokens only, never raw hex in components.

## 1. Project overview and design objectives
- **Purpose:** Ask questions of private documents and get cited, verifiable answers; let maintainers benchmark retrieval quality.
- **Primary success action:** Ask a question and verify an answer by opening a citation.
- **Objectives:** (1) User sees which document/page backs every claim without leaving the chat (≤1 click). (2) Upload→"ready to ask" state clear within 1 s of completion. (3) Composer visible without scroll at 1280×720. (4) Eval results readable in ≤5 s (metric, delta vs baseline). (5) WCAG 2.2 AA; all motion has a reduced-motion variant.
- **Constraints:** Desktop-first, mobile-usable; stack assumed React + Vite + Tailwind + CSS variables `[UNVERIFIED: confirm in memory.md]`; streaming over SSE.
- **Assumptions:** single-user v1; English UI; PDF viewer arrives in Phase 7 (placeholder drawer until then).

## 2. Audience and core user journeys
| Segment | Device | Context |
|---|---|---|
| Analyst/Support | Laptop 1280–1920px, some tablet | Verification-heavy, long sessions |
| Maintainer | Desktop ≥1440px | Compares configs, reads tables |

**J1 (critical):** Library → upload file → watch ingest progress → Chat → ask → read streamed answer → click citation chip → see source passage (+page).
**J2:** Eval → pick run → compare with baseline → inspect failing questions → open retrieved chunks.
**J3:** Library → delete/re-ingest document.
Accessibility: keyboard-only complete flows; screen-reader live region for streaming; no localisation beyond LTR English in v1 (use logical CSS properties for future RTL).

## 3. Research findings and selected references
No external site inspected this session; patterns below are from general knowledge.
| Source | Status | Pattern | Decision | Where | Licence |
|---|---|---|---|---|---|
| Footnote/citation conventions in academic & editorial UIs | `[UNVERIFIED]` | Numbered inline markers + source panel | Adopt | Chat citations | n/a |
| Chat UIs (general) | `[UNVERIFIED]` | Left history, centre thread, composer bottom | Adapt: swap history for document scope selector | Chat | n/a |
| Observability dashboards (general) | `[UNVERIFIED]` | Metric cards + delta chips + sortable tables | Adopt | Eval | n/a |
| Motion Primitives / GSAP / 21st.dev etc. | `[UNVERIFIED]` | Rich scroll/text effects | **Reject**: product is a dense tool; effects hurt reading/speed | — | — |
Re-verify any library in §16 against current docs before installing.

## 4. Overall creative direction
- **Idea:** *"The Reading Room"*: a quiet archive desk where every claim is footnoted and the evidence is always within reach.
- **Personality:** calm, scholarly, precise, warm, trustworthy. **Not:** neon-AI gradients, glassmorphism, chatbot-bubble cartoons, purple-blue gradients, robot/sparkle iconography.
- **Mood:** printed paper, archival index cards, highlighter on a page.
- **Signature moment (one):** clicking a citation chip slides the source drawer in and **highlights the exact passage with a highlighter-sweep** (M-03).
- **Restraint rule:** no animation longer than 400 ms except streaming and progress; nothing animates on scroll.

## 5. Design principles and anti-patterns
| Principle | Testable implication |
|---|---|
| Evidence is first-class | Every answer paragraph has ≥1 citation chip or an explicit "no source found" state |
| Reading before chrome | Answer column 62–72ch; UI chrome ≤ 20% of viewport width |
| Honest states | Retrieval-only/low-confidence answers show a visible confidence note |
| Numbers are legible | Metrics use mono tabular figures, always with units and baseline delta |
| Calm motion | Motion only to orient/confirm (see §12) |
| Keyboard parity | Every pointer action has a key path |
**Anti-patterns → replacement:** gradient hero text → solid ink headings · chat bubbles with avatars → full-width message blocks with role label · spinner-only loading → skeleton + stage label ("Retrieving 5 passages…") · tooltips as only citation preview → persistent drawer · color-only status → icon + text.

## 6. Colour tokens and semantic usage
| Token | Role | Light | Dark | Usage | Pair / ratio* |
|---|---|---|---|---|---|
| `--bg` | App background | #F6F2EA | #14130F | page | ink on bg ≈ 15:1 |
| `--surface` | Cards, composer | #FFFDF8 | #1D1B16 | panels | ink on surface ≈ 16:1 |
| `--surface-2` | Hover/inset | #EFE9DC | #26231D | rows, code | — |
| `--ink` | Body text | #1B1A17 | #EFE9DC | text | — |
| `--ink-muted` | Secondary | #5E594F | #A8A294 | captions, meta | ≈ 5.6:1 on bg (≥4.5) |
| `--border` | Hairlines | #DDD4C3 | #38342B | dividers | decorative |
| `--accent` | Primary action, links, focus | #14524F | #6CC4BC | buttons, active nav | white on accent ≈ 8:1 |
| `--accent-ink` | Text on accent | #FFFFFF | #0E1F1E | button label | — |
| `--mark` | Highlighter (source passage) | #F3D86B | #8A7424 | cited text bg | ink on mark ≈ 11:1 |
| `--cite` | Citation chip bg | #E4EEEC | #1F2F2D | chips | accent on cite ≥ 4.5 |
| `--success` | Good metric/ready | #2F6B3B | #7BC98B | status | icon+text |
| `--warn` | Low confidence/delta ↓ small | #8A5A00 | #E0B04A | notes | icon+text |
| `--danger` | Errors/regressions | #A3302B | #F08A84 | errors | icon+text |
*Ratios are estimates `[UNVERIFIED]`; verify every pair with axe/contrast tool before sign-off.
**States:** hover = `--surface-2` bg or accent −8% L; active = accent −14% L; focus = 2px `--accent` ring, 2px offset (+1px `--bg` gap); disabled = 45% opacity + `cursor:not-allowed` (not the only cue); selected = 3px left accent bar + `--surface-2`.
**Rules:** no gradients anywhere; overlays = `rgba(20,19,15,0.45)`; dark mode follows `prefers-color-scheme` with manual toggle (persist in localStorage).

## 7. Typography system
| Family | Role | Source/licence |
|---|---|---|
| Newsreader (variable) | Display, headings, answer text | Google Fonts, OFL `[UNVERIFIED]` |
| Instrument Sans | UI labels, buttons, nav | Google Fonts, OFL `[UNVERIFIED]` |
| JetBrains Mono | Citations, metrics, code, IDs | OFL `[UNVERIFIED]` |
| Role | Font/weight | Size desktop / mobile | Line height | Tracking |
|---|---|---|---|---|
| Display | Newsreader 500 | 2.5rem(40) / 2rem(32) | 1.1 | −0.01em |
| H1 | Newsreader 500 | 1.75rem(28) / 1.5rem | 1.2 | −0.005em |
| H2 | Newsreader 600 | 1.25rem(20) / 1.125rem | 1.3 | 0 |
| Answer body | Newsreader 400 | 1.125rem(18) / 1.0625rem | 1.65 | 0 |
| UI body | Instrument Sans 400 | 0.9375rem(15) | 1.5 | 0 |
| Label | Instrument Sans 600 | 0.75rem(12) | 1.3 | +0.06em, uppercase |
| Caption | Instrument Sans 400 | 0.8125rem(13) | 1.4 | 0 |
| Mono/metric | JetBrains Mono 500 | 0.875rem(14), `font-variant-numeric: tabular-nums` | 1.4 | 0 |
Loading: self-host WOFF2 subsets, `font-display: swap`, preload Newsreader 400 + Instrument Sans 400; fallbacks `Georgia, serif` / `system-ui, sans-serif` / `ui-monospace, monospace`. Use `text-wrap: balance` on headings, `pretty` on answers. Max line 72ch.

## 8. Spacing, grid, sizing and layout rules
- Base unit 4px; scale: 4, 8, 12, 16, 24, 32, 48, 64, 96.
- Containers: app shell full width; chat column max 720px centred; library/eval max 1200px.
- Grid: desktop 12-col, 24px gutter, 32px margin; tablet 8-col 20px/24px; mobile 4-col 16px/16px.
- Shell: left nav 232px (collapsed 64px); right source drawer 420px (full-screen sheet on mobile).
- Section padding: 32px (desktop) / 20px (mobile). Radius: 6px controls, 10px cards, 999px chips. Borders 1px `--border`; shadows only on drawer/menus: `0 8px 24px rgba(20,19,15,.12)`.
- Z-index: base 0 · sticky 10 · drawer 30 · modal 40 · toast 50.
- Touch targets ≥ 44×44 (min 24×24 for dense table controls).

## 9. Component inventory and specifications
| Component | Variants | States | Source | Pages |
|---|---|---|---|---|
| AppShell/NavRail | expanded/collapsed | default, active item | custom | all |
| Button | primary, secondary, ghost, danger | default, hover, focus, active, disabled, loading | custom | all |
| Composer | single/multi-line | default, focus, streaming (stop btn), disabled | custom | Chat |
| MessageBlock | user, assistant | streaming, complete, error, abstained | custom | Chat |
| CitationChip | `[1] doc · p.4` | default, hover, focus, active(open) | custom | Chat |
| SourceDrawer | passage view, PDF view (Ph.7) | closed/open/loading/error | custom | Chat |
| ScopeSelector | all docs / selected | open, selected | custom | Chat |
| UploadDropzone | idle, dragover, uploading, error | per-file progress | custom | Library |
| DocumentRow/Table | status: queued, parsing, indexing, ready, failed | selected, hover | custom | Library |
| MetricCard | value, delta | up/down/neutral | custom | Eval |
| RunTable | sortable | sorted, expanded row | custom | Eval |
| BarCompare | baseline vs run | hover tooltip | custom SVG | Eval |
| Toast, Skeleton, EmptyState | — | — | custom | all |
**Key specs:**
- *CitationChip:* height 24px, padding 0 8px, `--cite` bg, mono 12px, radius 999px; content `n · filename(truncate 18ch) · p.X`; Enter/Space opens drawer; `aria-controls="source-drawer"`; motion M-03.
- *MessageBlock (assistant):* no bubble; 2px left rule `--border`; role label (Label style) "ANSWER"; answer text 18px serif; citation chips inline after sentence; footer row: copy, retrieved-passages toggle, timing (mono) e.g. `412 ms · 5 passages`.
- *MessageBlock (user):* left-aligned, `--surface-2` bg, radius 10px, Instrument Sans 15px.
- *Abstained state:* warn icon + "The documents don't contain enough information to answer this." + nearest passages list.
- *Composer:* sticky bottom, `--surface`, 1px border, radius 10px, min-height 56px, auto-grow to 200px; Enter send, Shift+Enter newline, Esc stop stream.
- *SourceDrawer:* header (doc name, page, close), body = passage with `--mark` highlight on the matched span; prev/next passage buttons; "Open page" button disabled until Phase 7.
- *MetricCard:* label (Label style), value (Display-mono 28px), delta chip (`▲ +0.04` success / `▼ −0.02` danger, with text, never color-only), mini sparkline optional.

## 10. Page-by-page layouts and section order
**Chat `/`** goal: ask & verify.
```
[NavRail 232][        Thread (max 720)         ][ SourceDrawer 420 (on demand) ]
              [ ScopeSelector                 ]
              [ MessageBlocks…                ]
              [ Composer (sticky)             ]
```
Sections: scope bar → thread (empty state: 3 example questions drawn from library + "Upload documents" link) → composer. Mobile: drawer = bottom sheet 85vh; nav → top bar + menu.
**Library `/library`** goal: manage corpus. Order: header + "Upload" button → Dropzone (full width, 160px high) → filters (search, status) → DocumentTable (columns: name, type, pages, chunks, added, status, actions). Empty state: dropzone enlarged with supported formats and size limit.
**Eval `/eval`** goal: judge quality. Order: run selector + "Compare with baseline" → 4 MetricCards (Hit@5, MRR, Faithfulness, p95 latency) → BarCompare (Hit@K for K=1,3,5,10) → RunTable (config summary, metrics, date) → Failures panel (question, expected source, retrieved top-5, judge notes). Wide tables scroll in own container.

## 11. Responsive behaviour
| Name | Min width | Columns | Navigation | Type | Imagery/other | Motion |
|---|---|---|---|---|---|---|
| sm | 0 | 4 | top bar + sheet menu | mobile sizes | drawer = bottom sheet | M-03 becomes vertical slide-up |
| md | 768px | 8 | collapsed rail 64px | desktop sizes | drawer overlays thread | as spec |
| lg | 1100px | 12 | expanded rail | desktop | drawer pushes thread | as spec |
| xl | 1440px | 12 | expanded | desktop | eval tables up to 1200px | as spec |
Pointer vs touch: citation preview-on-hover is **not** used; click/tap only. Hover affordances duplicated by focus styles. Landscape phones: composer max-height 40vh.

## 12. Motion design system and animation specifications
**12.1 Principles:** orient, confirm, connect. No decorative loops. Streaming is the only continuous motion.
**12.2 Tokens**
| Token | Value |
|---|---|
| `--dur-fast` | 120ms |
| `--dur-base` | 200ms |
| `--dur-slow` | 360ms |
| `--ease-out` | cubic-bezier(0.22, 1, 0.36, 1) |
| `--ease-in-out` | cubic-bezier(0.65, 0, 0.35, 1) |
| `--stagger` | 40ms (max 6 items) |
| `--distance` | 8px (small), 24px (drawer offset) |
**12.3 Animation register**
| ID | Element / Trigger | From → To | Props / timing | Reduced motion | Perf |
|---|---|---|---|---|---|
| M-01 | Assistant tokens / SSE chunk | opacity 0.4→1 per appended span | opacity, 120ms ease-out, batched per animation frame | no fade, instant append | append in rAF batches ≤ 60/s; no layout thrash |
| M-02 | Retrieval stage label / stage change | "Retrieving…"→"Generating…" | crossfade 120ms; skeleton shimmer 1.4s linear loop (stops when first token arrives) | static skeleton, no shimmer | CSS only |
| M-03 | CitationChip click → SourceDrawer open | drawer translateX(24px)+opacity 0 → 0/1, then `--mark` sweeps left→right over passage | drawer 200ms ease-out; mark `background-size` 0→100% 360ms ease-in-out delay 120ms | drawer fades 120ms; mark appears instantly | transform/opacity + background-size; reverse on close 120ms |
| M-04 | Upload row progress | width 0→n% | transform scaleX, 200ms linear steps; success → check icon scale 0.8→1 160ms | no scale, instant state | CSS |
| M-05 | Page/route enter | opacity 0, translateY 8px → 1/0; children stagger 40ms | 200ms ease-out | opacity-only 120ms or none | max 6 children |
| M-06 | Eval bars load | scaleY 0→1 from baseline | 360ms ease-out, stagger 40ms | instant | SVG transform |
| M-07 | Toast in/out | translateY 8px + opacity | 200ms in / 120ms out | opacity only | — |
**12.4 Timeline (M-03):** t0 click → t0 drawer starts → t120 mark sweep starts → t200 drawer settled → t480 sweep ends; focus moves to drawer heading at t0 (no waiting).
**12.5 Scroll-linked:** Not applicable: no scroll-driven effects by decision. Thread auto-scrolls to bottom only if user within 80px of bottom; otherwise show "Jump to latest" chip.
**12.6 Libraries:** CSS transitions + `@keyframes` for all above. Motion (framer-motion) is optional only for drawer presence/exit if React unmount animation is needed `[UNVERIFIED: verify current docs/version]`. GSAP rejected (no timelines/scroll-pinning needed).

## 13. Interaction states and microinteractions
| Component | Default | Hover | Focus-visible | Active | Disabled | Loading | Error | Success | Selected |
|---|---|---|---|---|---|---|---|---|---|
| Button primary | accent bg | accent −8%L | 2px ring | −14%L | 45% opacity | inline spinner 16px + label kept | — | brief check (1.2 s) | — |
| CitationChip | cite bg | border accent | ring | pressed inset | — | — | strikethrough + "source missing" | — | accent bg + accent-ink text |
| DocumentRow | transparent | surface-2 | ring on row | — | — | stage badge animates | danger icon + retry button | ready badge | left bar |
| Composer | border | border-strong | accent ring | — | grey, hint "Upload a document first" | stop button visible | inline error + retry | — | — |
**Keyboard:** `/` focus composer · `Enter` send · `Esc` close drawer / stop stream · `Alt+↑/↓` previous/next citation · `Tab` order: nav → scope → thread → composer → drawer (drawer traps focus while open on <lg, returns focus to invoking chip on close). Touch: no hover-only controls.

## 14. Accessibility and reduced-motion requirements
- Target WCAG 2.2 AA. Text contrast ≥ 4.5:1, UI components ≥ 3:1 (verify §6 pairs).
- Focus ring: 2px `--accent`, 2px offset, never removed. Skip link "Skip to conversation". Landmarks: `nav`, `main`, `aside` (drawer, `role="complementary"`, labelled). One `h1` per page.
- Streaming answer in `aria-live="polite"` region updated per sentence (not per token); completion announces "Answer complete, N sources". Errors `role="alert"`.
- Citation chip: `button` with accessible name "Source 1, Handbook.pdf, page 4".
- Reduced motion (`prefers-reduced-motion: reduce`): per-ID column in §12.3; global rule sets all durations to 0 except opacity ≤120ms; shimmer off.
- No flashing; no autoplay >5 s except streaming (stoppable via Esc/Stop button).
- Charts: provide table equivalent; patterns/labels, not color alone.

## 15. Performance and implementation constraints
| Metric | Budget |
|---|---|
| LCP | ≤ 2.0 s (4G, mid laptop) |
| CLS | ≤ 0.05 (reserve skeleton heights) |
| INP | ≤ 150 ms |
| JS initial | ≤ 150 KB gz; route-split Eval charts |
| CSS | ≤ 30 KB gz |
| Fonts | ≤ 3 families, ≤ 5 files, ≤ 120 KB total WOFF2 |
| Animation | 60 fps; transform/opacity only (exception M-03 background-size, small area) |
Virtualize lists >200 rows; debounce search 200ms. Support last 2 versions of Chrome, Edge, Firefox, Safari; iOS Safari 16+. No WebGL.

## 16. Recommended libraries and verified component references
| Library | Purpose | Verification | Licence | Note |
|---|---|---|---|---|
| React + Vite | app | `[UNVERIFIED]` | MIT | assumed |
| Tailwind CSS | utilities over CSS variables | `[UNVERIFIED]` | MIT | tokens in `:root` |
| Radix UI primitives | accessible dialog/menu/tabs | `[UNVERIFIED]` | MIT | use for focus mgmt |
| TanStack Query | data/SSE state | `[UNVERIFIED]` | MIT | — |
| react-markdown + remark-gfm | render answers | `[UNVERIFIED]` | MIT | sanitize output |
| react-pdf / PDF.js | viewer (Phase 7) | `[UNVERIFIED]` | Apache-2.0 | bbox highlight |
| Motion | optional exit animations | `[UNVERIFIED]` | MIT | only if needed |
Re-verify versions/install docs before adding; log additions in `memory.md`.

## 17. File-level implementation guidance
No repository inspected; proposed layout under `frontend/`:
`src/styles/tokens.css` (§6–8, 12.2 as CSS vars) · `src/components/{ui,chat,library,eval}/` · `src/routes/{Chat,Library,Eval}.tsx` · `src/lib/sse.ts` · `src/lib/api.ts` (typed to FastAPI schemas).
**Order:** tokens → AppShell → Button/Chip/Skeleton → Library (upload) → Chat (stream + citations + drawer) → Eval → a11y/perf pass. **Slices:** one PR per route. Don't add dependencies outside §16 without logging.

## 18. Acceptance criteria and visual quality checklist
| Area | Criterion |
|---|---|
| Chat | Streamed answer renders; each paragraph has citation or "no source" state; chip opens drawer with highlighted passage in ≤ 200 ms |
| Library | Upload shows per-file progress; failed file shows reason + retry; status updates without reload |
| Eval | Metrics show delta vs baseline with icon+text; failures list opens retrieved chunks |
| M-01…M-07 | Match §12.3; each has working reduced-motion variant (verify via emulation) |
| A11y | axe 0 critical/serious; full keyboard run of J1; screen-reader announces stream completion |
| Perf | Lighthouse ≥ 90 perf & ≥ 95 a11y on all three routes; budgets §15 |
| Visual | Tokens only (grep for raw hex = 0 in components); light/dark both reviewed; 360, 768, 1280, 1920 px checked |
**Definition of done:** criteria pass, tools above actually run with results logged in `memory.md`.

## Appendix
**Assumptions:** React/Tailwind stack; single-user; English only; fonts/licences unverified. **Open questions:** (1) Confirm frontend framework. (2) Is dark mode required for v1? (3) Brand name/logo? **Risks:** contrast estimates unverified; PDF highlight depends on Phase 7 bbox data. **Change log:** v1.0 initial.
