# Site design (notgeese.cc)

Binding values live in `site/src/styles/tokens.css` (same data in `tokens.json`). This file is
the rationale in brief.

## Color and themes

Every shade is a mix of `ink` and `bone`. No gradients, no transparency (except the drawer scrim).

| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `bone` | `#F9F7F3` | `#141414` | page background |
| `paper` | `#FFFFFF` | `#1C1C1B` | raised surfaces (tiles, panel) |
| `ink` | `#141414` | `#F9F7F3` | text, borders, shadows, stats |
| `accent` | `#DC143C` | `#DC143C` | crimson: accents, CTA, "in progress" |
| `graphite` | `#363635` | `#363635` | keyart placeholder background |
| `muted` | `#646362` | `#B4B3B0` | secondary text (≥ 5.6:1) |
| `muted-inverse` | `#B4B3B0` | `#646362` | secondary text on dark |
| `hairline` | `#D7D5D2` | `#3A3A38` | 1 px lines inside frames |
| `shadow-color` | `#141414` | `#363635` | shadow |

- Text on crimson: white for small text, black only Archivo Black ≥ 18 px.
- Theme switch in the header: system → light → dark, stored in `localStorage` (`ng-theme`),
  applied by an inline `<head>` script before first paint.

## Type

Google Fonts, `latin` + `latin-ext`, `font-display: swap`.
Archivo Black 400 (headings, caps, negative tracking), Space Grotesk 400/500/700 (body, quotes),
JetBrains Mono 400/700 (metadata, labels always caps, nav, UI).

| Level | Desktop / mobile | Line height | Tracking | Face |
| --- | --- | --- | --- | --- |
| Hero | 80 / 34 px | 0.92–0.95 | −0.035em | Archivo Black |
| Hero secondary | 40 / 22 px | 1.0 | −0.03em | Archivo Black |
| Section heading | 56 / 30 px | 1.0 | −0.03em | Archivo Black |
| Panel heading | 40–44 / 28 px | 0.98 | −0.03em | Archivo Black |
| Tile title | 22 / 20 px | 1.05 | 0 | Archivo Black |
| Stat numbers | 56 / 38 px | 1.0 | 0 | Archivo Black |
| Quote | 21 / 15 px | 1.45–1.5 | 0 | Space Grotesk |
| Body | 16–17 / 14 px | 1.55–1.6 | 0 | Space Grotesk |
| Mono labels | 12 / 10 px | — | 0.14–0.18em | JetBrains Mono |
| Mono metadata | 11 / 10 px | — | 0.10em | JetBrains Mono |

## Grid and form

- Spacing: multiples of 4 px (`4 8 12 16 20 24 28 32 40 48 64 72 80`).
- Desktop 1440: 80 px margins, max 3 columns, gap 28. Mobile 390: 20 px margins, 1 column, gap 20.
  Tile min 280 px; under 700 px one column. `scrollbar-gutter: stable`.
- Borders always `3px solid var(--ink)`. Hard shadows, no blur: 8 px desktop, 7 px mobile.
- `border-radius: 0` everywhere (only exception: mobile drawer handle 52×5 px, radius 3).

## Components

- **Hero:** two columns from 1100 px, one below. Left: crimson title (scales with its column), ink
  secondary line, 148×10 crimson rule, lead. Right: every game cover, shuffled per visit, in two
  columns drifting down at different speeds, faded at top and bottom. A cover opens its panel;
  hovering one stops its column and shows the title. Mouse-only (`aria-hidden`, out of tab order),
  still under `prefers-reduced-motion`.
- **Process ("Proces"):** between stats bar and game list. Eight clickable step blocks joined by
  6 px ink bars, no autoplay: chosen block crimson and lifted, earlier blocks bone, bars before it
  crimson. Below: number, title and text of the chosen step. Under 1200 px blocks show numbers only.
- **Workshop ("Pracownia"):** after Process. Two-column intro, then a window (3 px border, hard
  shadow, bar labelled "Pracownia") holding a read-only copy of the /admin/ game view: same markup and
  `workspace.css` (rules apply to `#workspace` and `.ws-demo`). Whole Shotgun Cop Man, laid out by the
  shared workspace code into `/pracownia-demo.json` (fetched when the section comes near), states
  drawn at random per visit. Groups, sequences, search, state filter, drafts-only, view modes,
  PL-only, paging, accept/edit/undo work in the browser only; no save, refresh or export buttons.
- **Game tile:** Steam capsule on top (616:353), fixed-height description below a 3 px rule.
  Placeholder: `[KEYART]` label top-left + title initial at `rgba(255,255,255,0.13)` bottom-right.
  The whole tile is one `<a>`.
- **Detail panel:** ≥ 700 px right overlay `min(800px, 92vw)`; < 700 px bottom drawer (max 88%,
  scrim `rgba(20,20,20,0.58)`). Modal: `aria-modal`, focus trap, background scroll lock; 240 ms
  `cubic-bezier(0.2,0,0,1)`, honors `prefers-reduced-motion`. Own URL `/<slug>/`; closes on
  Escape, backdrop, 44×44 close button. Order: media carousel (16:9) → title → status and meta
  → game quote → description → download CTA → store links → metadata table.
- **Status badges** (`games/catalog.yaml` tone): `ready` accent fill; `testing` ink fill; `in-progress`
  2 px ink outline. No progress percentages.
- **Controls:** hit area ≥ 44×44; `:focus-visible` 3 px accent outline, 3 px offset (ink on red
  surfaces). Main CTA: accent background, Archivo Black ink text, 3 px border, 8 px shadow; hover
  shifts 4 px and shrinks shadow to 4 px. Filters/sort: custom `Dropdown.astro` (paper, 3 px
  border, hard shadow).

## Media

- Keyart in `site/public/keyart/<slug>/`, AVIF + WebP fallback, no JPG (`tools/keyart.py`).
- Cover 616×353 and 1232×706 (@2x); screenshots 1600×900.
- Carousel: CSS scroll-snap, no library; JS adds 44×44 arrows and ←/→ keys.

## Never

Gradients, blur or transparency (except the scrim); rounded corners; filled icons (outline 2 px
only; brand marks excepted); emoji; clickable `<div>` with `onClick`.
