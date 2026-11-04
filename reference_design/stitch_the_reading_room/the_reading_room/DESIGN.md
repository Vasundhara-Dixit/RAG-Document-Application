---
name: The Reading Room
colors:
  surface: '#fff8f0'
  surface-dim: '#e2d9c8'
  surface-bright: '#fff8f0'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#fcf3e1'
  surface-container: '#f6eddb'
  surface-container-high: '#f1e7d6'
  surface-container-highest: '#ebe1d0'
  on-surface: '#1f1b11'
  on-surface-variant: '#404847'
  inverse-surface: '#353024'
  inverse-on-surface: '#f9f0de'
  outline: '#707978'
  outline-variant: '#bfc8c7'
  surface-tint: '#2e6764'
  primary: '#003a38'
  on-primary: '#ffffff'
  primary-container: '#14524f'
  on-primary-container: '#8bc4bf'
  inverse-primary: '#98d1cd'
  secondary: '#6f5d00'
  on-secondary: '#ffffff'
  secondary-container: '#fde273'
  on-secondary-container: '#766300'
  tertiary: '#2b3533'
  on-tertiary: '#ffffff'
  tertiary-container: '#424b4a'
  on-tertiary-container: '#b1bbb9'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#b3ede9'
  primary-fixed-dim: '#98d1cd'
  on-primary-fixed: '#00201e'
  on-primary-fixed-variant: '#104f4c'
  secondary-fixed: '#fde273'
  secondary-fixed-dim: '#e0c65b'
  on-secondary-fixed: '#221b00'
  on-secondary-fixed-variant: '#544600'
  tertiary-fixed: '#dbe5e3'
  tertiary-fixed-dim: '#bfc9c7'
  on-tertiary-fixed: '#141d1c'
  on-tertiary-fixed-variant: '#3f4947'
  background: '#fff8f0'
  on-background: '#1f1b11'
  surface-variant: '#ebe1d0'
typography:
  headline-xl:
    fontFamily: Newsreader
    fontSize: 40px
    fontWeight: '400'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Newsreader
    fontSize: 30px
    fontWeight: '400'
    lineHeight: 38px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Newsreader
    fontSize: 28px
    fontWeight: '500'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Newsreader
    fontSize: 22px
    fontWeight: '500'
    lineHeight: 30px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Newsreader
    fontSize: 19px
    fontWeight: '400'
    lineHeight: 30px
  body-md:
    fontFamily: Newsreader
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
  body-sm:
    fontFamily: Newsreader
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  ui-label-lg:
    fontFamily: Work Sans
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  ui-label-md:
    fontFamily: Work Sans
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  ui-label-sm:
    fontFamily: Work Sans
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
  citation-code:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.02em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.875rem
  space-lg: 1.25rem
  space-xl: 2rem
---

## Brand & Style

This design system draws direct inspiration from archival reading rooms, curated rare-book libraries, and academic research stations. It deliberately rejects ephemeral generative-AI tropes—banishing electric purple gradients, frosted glass blur overlays, floating chatbot speech bubbles, and decorative sparkle icons. 

In their place, the interface evokes the intellectual weight, physical permanence, and calm focus of physical scholarship: hot-metal typography, rag paper, index card files, hand-annotated margins, and archival preservation materials. The emotional resonance is quiet, dependable, deeply focused, and authoritative. It treats document question-answering not as a consumer novelty, but as rigorous research synthesis with transparent evidentiary trails.

Key aesthetic pillars:
- **Paper & Ink Tactility:** Rich, warm off-white grounds paired with deeply saturated charcoal ink tones, entirely avoiding clinical cold greys or hyper-saturated digital hues.
- **Archival Precision:** Structural hairline rules, crisp tabular metrics, index-tab geometry, and deliberate bibliographic citation typography.
- **Physical Annotation Metaphors:** Citations, provenance tokens, and query matches borrow visually from fountain-pen marginalia, paper slips, and soft yellow wax highlighters.

## Colors

The palette is tuned around tactile reading substrates, deep plant-based inks, and physical research tools:

- **Background (`#F6F2EA`):** Warm unbleached rag paper canvas. Serves as the global backdrop to reduce visual fatigue during long synthesis sessions.
- **Surface (`#FFFDF8`):** Archival card stock. Slightly elevated, clear ivory plane used for primary reading panels, answer cards, and document viewports.
- **Surface Inset / Subtle (`#EFE9DC`):** Pressed pulp tone for table headers, embedded query bars, code blocks, and hover states.
- **Ink Primary (`#1B1A17`):** Warm lampblack printing ink for primary headings, synthesized body copy, and high-priority data.
- **Ink Muted (`#5E594F`):** Faded editorial ink for metadata, timestamps, author lines, and secondary structural annotations.
- **Border / Hairline (`#DDD4C3`):** Neutral bone-ruled separator line. Provides structural division without visual aggression.
- **Primary Accent (`#14524F`):** Deep scholar forest green. Applied to primary actionable controls, verified source indicators, active selection tabs, and high-confidence metrics. Text on this accent must always be `#FFFFFF`.
- **Annotation Mark (`#F3D86B`):** Archival wax highlighter yellow. Applied strictly for synthesized excerpts, search query hits, and direct verbatim quote highlights.
- **Citation Tint (`#E4EEEC`):** Muted pale celadon wash for inline reference pills, source drawer chips, and provenance markers.

## Typography

The typographical structure balances long-form academic readability with the crisp density required for technical search-and-retrieval workflows:

- **Editorial Reading Voice (Newsreader):** Handled by an optical editorial serif. Used for syntheses, generated answers, document titles, and narrative excerpts. Its italic forms are expressive and traditional, ideal for direct source blockquotes.
- **Instrumental UI Navigation (Work Sans):** Clear, humanist, and unornamented. Handles navigation trees, filter headers, metadata columns, table controls, and button labels without competing with the serif narrative.
- **Bibliographic & Retrieval Rigor (JetBrains Mono):** Monospaced precision reserved for chunk IDs, cosine similarity metrics, page coordinates (e.g., `p. 142 § 3`), citation tokens, token counts, and latency readouts.

Styling guidelines:
- Synthesized output should default to `body-lg` with an extended line-height (`30px`) to mimic luxury book typography and support effortless scanning.
- Numerical indices inside citations are always tabular and set in monospaced glyphs to prevent baseline jumps.

## Layout & Spacing

The layout is built for scholarly desktop ergonomics, accommodating a split-screen or multi-pane paradigm: a persistent document corpus/index on the left, an evidentiary synthesized response pane in the center, and an original manuscript/PDF facsimile inspection panel on the right.

### Layout System
- **Desktop (Multi-Column Workspace):** A 12-column rigid grid with a max width of `1680px`. The canonical desktop workspace splits into:
  - Navigational archive drawer / catalog filter: 3 columns.
  - Synthesis & query answering ledger: 5 columns.
  - Source verification & grounding viewer: 4 columns.
- **Tablet / Split View:** 8 columns with 1rem gutters; left navigation collapses to an indexed pull-tab, and synthesis/document viewers share an equal 50/50 balance.
- **Mobile:** 4 columns with stacked layout. Answers display sequentially, and tapping a citation sheet drawer pulls up source cards from the bottom.

### Rhythm
Information density leans academic and compact. Component internal paddings employ tight geometric increments (`0.25rem` to `1.25rem`), prioritizing visible context and cross-referencing capabilities over excessive empty expanses. Vertical margins between sections follow strict editorial ledger lines ruled by 1px borders.

## Elevation & Depth

This system avoids floating, drop-shadowed plastic layers. Visual hierarchy is established via material stratification, printed ink contrast, and delicate boundary lines:

1. **Surface Layering:**
   - **Base Canvas (`#F6F2EA`):** The foundational physical desk plane.
   - **Active Document / Card (`#FFFDF8`):** The primary paper leaf lying atop the desk. Separation is achieved through a crisp `1px solid #DDD4C3` rule rather than diffuse shadows.
   - **Recessed Areas (`#EFE9DC`):** Pressed depressions for search inputs, table headers, and citation source boxes.
2. **Bibliographic Shadow (Special Case):**
   - For floating source tooltips, popover citation previews, or modal card drawers, the system allows a single, precise, ink-tinted offset shadow rather than ambient blur:
     `box-shadow: 0 4px 12px -2px rgba(27, 26, 23, 0.08), 0 1px 3px 0 rgba(27, 26, 23, 0.04);`
3. **Framing Rules:**
   - Visual priority is reinforced by physical rule weights: primary panels use `1px solid #DDD4C3`; active focus elements switch to `1px solid #14524F`; active highlighted text uses a crisp bottom underline rule alongside the `#F3D86B` marker tint.

## Shapes

The shape system mimics physical paper stationery, trimmed card indexes, book bindings, and adhesive research labels.

- **Base Radius (0.25rem / 4px):** Applied to primary cards, action buttons, input fields, and modal containers. This delivers a tailored, near-rectilinear cut that references guillotined paper and catalog cards.
- **Chip & Citation Corners (0.125rem / 2px or 0.25rem / 4px):** Index citation tokens and provenance badges remain disciplined and squared, avoiding round pill capsules.
- **Zero Radius Elements:** Dividers, source viewing frames, split-screen panels, and vertical tab stops maintain sharp `0px` corners to reinforce architectural structural alignment.

## Components

### Buttons
- **Primary Action (Scholar Button):** Solid `#14524F` fill with `#FFFFFF` text. Clean `4px` corner radius. Font set in Work Sans (`ui-label-lg`). Border: `1px solid #0E3D3A`. Hover: `#0E3D3A`. Pressed: `#092725`.
- **Secondary (Card Action):** `#FFFDF8` surface with `1px solid #DDD4C3` hairline, `#1B1A17` text. Hover brings `#EFE9DC` background and `#5E594F` border.
- **Ghost / Action Link:** Transparent fill, `#14524F` text with a subtle dotted underline or adjacent glyph.

### Citation Chips & Provenance Tokens
- Grounding citations embedded in answers appear as inline tags:
  - Font: JetBrains Mono (`citation-code`).
  - Background: `#E4EEEC`.
  - Border: `1px solid #C4D7D4`.
  - Text: `#14524F`.
  - Padding: `1px 5px`.
  - Radius: `2px`.
  - Hover: Background darkens slightly (`#D3E3E0`) and triggers the provenance preview popover.

### Text Highlighter Marks
- Direct verbatim quotes or retrieved passages:
  - Background: `#F3D86B`.
  - Text: `#1B1A17`.
  - Padding: `0 2px`.
  - Border-bottom: `1px solid #DFC048`.

### Input Fields & Search Bars
- Inquiry box evokes an academic search ledger or index catalog input:
  - Background: `#FFFDF8`.
  - Border: `1px solid #DDD4C3`.
  - Text: `#1B1A17` in Newsreader body scale. Placeholder: `#5E594F` italicized.
  - Active / Focus: Border transitions to `1.5px solid #14524F` with no fuzzy glow ring. An optional subtle `0 0 0 1px #14524F` inset keeps borders crisp.

### Cards & Archival Containers
- **Synthesis Sheet:** Outer border `1px solid #DDD4C3`, background `#FFFDF8`. Header region is partitioned by a full-width `1px` bottom border line separating metadata (query latency, model provenance, and indexed corpora) from the reading narrative.
- **Source Excerpt Card:** Sits inside the grounding viewer. Surface `#FFFDF8`, hairline border `#DDD4C3`. Left-hand edge features a solid vertical `3px` stripe in `#14524F` (for top citations) or `#DDD4C3` (for secondary matches).

### Lists & Key-Value Metadata Tables
- Monospaced numeric alignments with hanging indents.
- Metadata rows (chunk score, tokens, author, collection, date) alternate with subtle `#EFE9DC` row borders, using uppercase JetBrains Mono labels in `#5E594F` and tabular values in `#1B1A17`.

### Selection Controls (Checkboxes & Radios)
- Sharp, understated boxes (`2px` radius) with `1px solid #5E594F`.
- When checked: Fill `#14524F`, featuring a crisp `#FFFFFF` tick mark. No outer halos.