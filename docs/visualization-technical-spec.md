# Career Ladder Visualization - Rendering Spec

A self-contained specification for building an interactive HTML career-ladder visualization from a structured resume JSON. This document covers the input contract (JSON schema), page-level content presentation rules, and chart-rendering rules (geometry, encoding, palette, interactivity).

The output is a single self-contained HTML file. No external runtime dependencies except Google Fonts. All chart drawing is inline SVG; all interactivity is plain JS; styling is plain CSS (no framework).

---

## 1. Overview

The page has two co-equal halves:

1. **Chart card** (top, sticky) - an interactive infographic showing the candidate's career progression as bars across two axes:
   - **X** = time (year)
   - **Y** = strata (career level: P1 Entry Professional through C-Level)
   - **Bar width** = role duration
   - **Bar color/stripes** = professional sphere(s) the role contributed to

2. **Textual narrative** (below) - the full resume content (hero, experience, education) laid out as readable prose.

The two halves are linked: clicking a bar in the chart scrolls to and highlights the matching role's article. Hovering a bar shows a tooltip with role details.

---

## 2. Input contract - JSON schema (v1.0)

The renderer expects a structured JSON of the shape below. Treat the schema as a contract: the renderer reads from these field paths and assumes their types. Unknown fields are ignored; missing optional fields default to safe values.

```json
{
  "$schema_version": "1.0",
  "generated": "YYYY-MM-DD",
  "source": "filename.pdf (uploaded resume, treated as sole source of truth)",
  "taxonomy_source": "job_families_and_industries.json v1.0",

  "candidate": {
    "name": "Full Name",
    "contact": {
      "phone": "+... or null",
      "email": "name@... or null",
      "linkedin": "https://linkedin.com/in/... or null",
      "github": "... or null",
      "portfolio": "... or null",
      "location": "City, Country (verbatim from resume)",
      "relocation": "null unless source resume states it (and even then, do not render)",
      "work_authorization": "null unless source resume states it"
    },
    "summary": "verbatim summary paragraph from resume if present",
    "areas_of_expertise": ["..."],
    "education": [
      { "institution": "...", "degree": "...", "field": "..." }
    ],
    "certifications": [
      { "name": "...", "issuer": "...", "date": "... or null" }
    ],
    "languages": ["..."],
    "honors": ["..."],
    "tech_stack": {
      "general_purpose": ["..."],
      "domain_specific": ["..."]
    }
  },

  "roles": [
    {
      "id": "role_1",
      "company": "Company name (current name)",
      "company_history_note": "Optional. If company was previously known by other names, render as italic line under company.",
      "title": "Full title from resume",
      "title_history_note": "Optional. For consolidated multi-title entries.",
      "location": "City / Remote / Hybrid (verbatim if present)",
      "country": "Country or null",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM or 'current'",
      "is_current": true,
      "single_sentence": false,
      "is_estimated": false,
      "duration_months": 21,
      "duration_label": "1 year 9 months",

      "narrative_summary": null,
      "narrative_bullets": [
        "Verbatim bullet from resume...",
        "Another verbatim bullet..."
      ],

      "strata": {
        "code": "M5",
        "name": "Director",
        "rank": 8
      },

      "family_tags": [
        {
          "family_id": "human_resources",
          "family_name": "Human Resources & People Operations",
          "weight": 0.7
        }
      ],

      "industry": {
        "id": "technology_software",
        "name": "Technology & Software"
      },

      "role_type": {
        "value": "IC | People Manager"
      },

      "render_policy": {
        "on_chart": true,
        "in_experience_text": true
      },

      "connector": {
        "same_employer_as_previous": true,
        "move_type_from_previous": "promotion | lateral | company_change | role_change",
        "previous_role_id": "role_2"
      }
    }
  ],

  "internships": [ /* same shape as roles, optional */ ],

  "aggregates": {
    "career_start": "YYYY-MM",
    "career_end": "current (YYYY-MM)",
    "career_length_months": 121,
    "career_length_label": "10 years 1 month",
    "sum_of_tenure_months": 113,
    "sum_of_tenure_label": "9 years 5 months",
    "role_count": 5,
    "employer_count": 4,
    "peak_strata": { "code": "M5", "name": "Director", "rank": 8 },
    "professional_spheres_ranked_by_dominant": [
      {
        "rank": 1,
        "color": "#75a426",
        "family_id": "human_resources",
        "family_name": "Human Resources & People Operations",
        "months": 113,
        "months_label": "9 years 5 months"
      }
    ]
  }
}
```

### Strata rank reference (13-level ladder, low → high)

Ranks run **0 through 12 inclusive**. Rank 0 (`P1`) was added in leveling-framework v3.0 (2026-08-09); ranks 1-12 were deliberately left unrenumbered so every previously generated `structured.json` and chart axis stays valid. Never treat rank 1 as the floor - a renderer that assumes a minimum rank of 1 will drop or mis-place any `P1` role.

| Code | Name | Rank |
|---|---|---|
| P1 | Entry Professional | 0 |
| P2 | Junior | 1 |
| P3 | Middle | 2 |
| P4 | Senior | 3 |
| P5 | Lead | 4 |
| P6 | Principal | 5 |
| M3 | Team Lead | 6 |
| M4 | Manager | 7 |
| M5 | Director | 8 |
| M6 | Senior Director | 9 |
| E7 | Vice President | 10 |
| E8 | Senior Vice President | 11 |
| C-Level | C-Level | 12 |

Codes and names above are copied verbatim from `reference-data/leveling-framework.json` and are the canonical strings that appear in `strata.code` / `strata.name`. Note the top row in particular: the code is `C-Level`, not `C` - that string must never change at the data layer (JSON, `DATA.strata_bands`, any comparison or lookup).

At the axis-label level, though, `C-Level` is the one code that's noticeably wider than the rest of the column (7 characters vs. the 2-3 of every other rank, since it doubles as its own name) - render it shortened to `C` in the `#strata-axis` overlay specifically (§5.4). This is a display-only substitution made at the point the label's `textContent` is set; it must not leak into the data or into any renderer comparison.

The renderer reads `strata.rank` for Y-axis positioning. The codes/names are just labels.

---

## 3. Page structure & layout

The HTML is a single self-contained file. Sections in order from top to bottom:

```
┌─────────────────────────────────────────────┐
│  HERO                                       │  ← name + contacts + location
├─────────────────────────────────────────────┤
│  CHART CARD (sticky, max-width 880px)       │
│  ├─ Tenure header                           │
│  ├─ Ladder frame                            │
│  │  ├─ Ladder wrap (SVG inside)             │
│  │  └─ Strata axis overlay (HTML)           │
│  ├─ Legend (pill row)                       │
│  └─ Hint line                               │
├─────────────────────────────────────────────┤
│  EXPERIENCE                                 │  ← reverse-chrono articles
│  ├─ <article id="role_1">                   │
│  ├─ <article id="role_2">                   │
│  └─ ...                                     │
├─────────────────────────────────────────────┤
│  EDUCATION                                  │  ← no dates
│  └─ certifications (inline)                 │
├─────────────────────────────────────────────┤
│  HONORS / TECH STACK (conditional)          │  ← omit if no data
└─────────────────────────────────────────────┘
```

### Sticky chart card

- `.chart-card { position: sticky; top: 0; z-index: 20; max-width: 880px; }`
- As the user scrolls through the experience text, the chart stays visible at the top - clicking bars to navigate stays usable from any scroll position.
- Padding: `18px 8px 8px`.

### Page width

- Max-width 880px centered on every section, for consistent reading column width.

### Page density & dividers (UPDATED 2026-07-19)

- Hero is center-aligned: name, contacts row, and location line all `text-align: center`. Tight padding (~20px top, ~12px bottom reference values); ~6px gap between name and contacts row.
- Divider lines (`border-bottom`) appear ONLY under the three section headers **Experience**, **Education**, **Tech Stack** (`.section-title`). No divider between individual role articles (whitespace/padding only), none between hero and chart card, none between chart card and Experience.
- Tenure header (stats row above the chart): center-aligned, both stat lines at the SAME font size (12px reference), bold applied only to the numeric values via `<b>` - not the whole line. Wording: `Career path span <b>X years Y months</b> · <b>N roles</b> · <b>M employers</b>` then `Peak job level · <b>CODE Name</b>` on the next line. Bottom padding on this row is kept near-zero so it reads as directly attached to the chart below it.
  - **C-Level exception (added spec v1.6)**: `CODE Name` renders as `C-Level C-Level` if built naively, since `strata.code` and `strata.name` are the identical string at that one rank. Render the peak line as just `C-Level` (once) when `peak_strata.code === peak_strata.name`; otherwise `code + " " + name` as normal. Do not apply the axis overlay's `C-Level` → `C` shortening (§5.4) here - the tenure header has room for the full word.

---

## 4. Content presentation rules (LOCKED)

These rules govern what gets rendered. They protect the candidate from incorrect representation and the page from clutter.

### 4.1 Verbatim bullets

`narrative_bullets` in each role are rendered VERBATIM in `<ul class="role-bullets">`. **Never paraphrase, combine, reword, truncate, or drop "etc."** Sequence may change (e.g. reverse-chrono ordering of roles), but content of each bullet never changes.

### 4.2 Role-summary panel (AI synthesis)

When a role has **8+ bullets**, compose a 2-3 sentence TL;DR and render it as a gray panel with a 3px left border above the bullet list.

```html
<p class="role-summary">Composed summary prose goes here.</p>
```

The "AI SYNTHESIS" label is added automatically by a CSS `::before` pseudo-element on `.role-summary`. **Do NOT add a `<span>` containing the label text inside the paragraph** - that produces a duplicate label.

```css
.role-summary::before {
  content: "AI SYNTHESIS";
  /* ...small-caps style... */
}
```

This is the ONLY composed prose allowed in the experience section. Roles with <8 bullets get no summary - bullets alone speak for themselves. The label makes clear which content is verbatim from the candidate vs. composed by the renderer.

### 4.3 Hero rule (STRICT)

Hero block contains ONLY:

1. Candidate's name
2. Contacts row - phone, email, LinkedIn - only those that exist in JSON
3. Location line - `candidate.contact.location` verbatim from JSON

Append `candidate.contact.work_authorization` ONLY if it's populated in the JSON. NEVER append:

- Relocation status ("open to relocation")
- Remote/hybrid preferences  
- Headline, objective, tagline, summary
- Any composed status text not in the JSON

### 4.4 Education - dates policy

**Never render education dates**, even if they appear in the JSON. This protects candidates from age-based screening.

Format: `Institution. Degree, Major/Field.`

Certifications follow as a single inline list under Education, separated by middle-dots.

### 4.5 Section conservatism (LOCKED)

Render these sections by default: **Hero, Chart Card, Experience, Education**.

Conditional sections (render if and only if both conditions hold):
- **Tech Stack** - JSON has `tech_stack` data AND candidate is in a tech-adjacent field
- **Honors** - JSON has `honors` data

**Never render these sections by default, even when the JSON has data for them:** Languages, Top Skills, Personal Characteristics, Interests, Driver's License, References. These are added ONLY on explicit user request per resume.

Adding sections without confirmation breaks user expectations and clutters the page. When in doubt, omit.

### 4.6 Company name rendering

- When `company_history_note` is populated (mid-employment rename like SoftwareHaus → ThePayPortal → CheckoutGate), render the rename history as a small italic line under the company name on the most-recent role at that employer.
- When `title_history_note` is populated (consolidated multi-title entries), render the title history as a small italic line under the company name.
- **Boomerang re-engagement (added spec v1.6)**: when Phase 1 has flagged a role as a non-adjacent return to an employer the candidate worked for earlier in a different role (see `reference/parsing.md`'s "Boomerang re-engagement" edge case), render a small italic line under the company name naming the earlier stint's title and dates (e.g. "Second engagement - previously Senior Data Scientist, Mar 2016 - Nov 2017"), same visual treatment as `company_history_note`. Without it, the same-employer staircase (§5.5, which groups by `company` across the whole role list regardless of adjacency) can read as one continuous tenure when the two stints are actually years apart.

### 4.7 Off-chart roles

When `role.render_policy.on_chart === false` AND `role.render_policy.in_experience_text === true`:
- Render the article normally in the experience section
- EXCLUDE the role from the chart's roles array

Common case: pre-career roles in a different professional family (e.g. retail jobs before an HR career) - they belong in the textual narrative but would distort the chart.

### 4.8 Internships

Optional `internships` array - render as a compact sub-block within Experience, NOT on the chart. Useful for early-career entries that aren't part of the strata-tracked main career.

---

## 5. Chart-rendering rules (LOCKED)

### 5.1 Fit-to-screen timeline

- The chart x-axis spans **exactly the on-chart career**:
  ```
  chartStart = Math.floor(earliest role start year)
  chartEnd   = Math.max(Math.ceil(latest role end year), today.year + 1)
  ```
- The whole career fits on one screen - **no horizontal scrolling**.
- SVG uses `width: 100%; height: auto` with `viewBox`. The browser scales it to fit the chart card automatically.

### 5.2 Locked viewBox total width → constant rendered band height

**The chart MUST render each strata band at the same CSS-pixel height regardless of how many years the candidate's career spans.** Horizontal density (years per pixel) intentionally varies with career length - a shorter career gets a more horizontally "zoomed-in" view, which is desirable. Vertical scale should NOT vary; a band at level P5 should look identical in height on every candidate's page.

**Why this matters.** With `width: 100%` + `preserveAspectRatio: xMidYMid meet`, vertical scaling is tied to horizontal scaling. If `viewBox` width varies per candidate (e.g. `vw = years × VB_PER_YEAR`), the browser scales the SVG up by `containerWidth / vw` - making bands appear taller for shorter careers and shorter for longer careers. Bands at the same logical level end up rendered at different heights.

**The fix.** Lock the **total viewBox width** to a constant, then derive `VB_PER_YEAR` from career span. The SVG's scale factor becomes identical across candidates, so vertical scaling is constant.

**Canonical values:**

- `TARGET_VB_TOTAL_WIDTH: 828` - chosen to match the actual rendered container width (chart-card 880 max-width minus 8px×2 padding minus 36px right reserve for the strata axis overlay). With this value, 1 viewBox unit ≈ 1 CSS pixel.
- `BAND_HEIGHT: 25` viewBox units → bands render at ~25 CSS px on every candidate.

If chart-card max-width or padding changes, recompute `TARGET_VB_TOTAL_WIDTH` to match.

**Canonical JS geometry block:**

```javascript
const CHART = {
  pad: { top: 24, right: 12, bottom: 56, left: 60 },
  BAND_HEIGHT: 25,
  TARGET_VB_TOTAL_WIDTH: 828
};

// Date -> fractional-year conversion. Start dates use "start of month";
// end dates (and "current") use "start of the NEXT month" (= end of this
// month). This asymmetry is intentional and load-bearing: it's what makes
// a role ending in month M line up exactly with a role starting in month
// M+1, with zero rendered gap. Reuse this SAME pair of helpers everywhere
// a role's date range becomes an x-coordinate - bar x1/x2, staircase
// arc-rect x1/x2, and the chartStart/chartEnd bounds below. Do not
// recompute the conversion inline in more than one place.
const startOfMonth = (year, month) => year + (month - 1) / 12;
const endOfMonth   = (year, month) => year + month / 12;

const today = DATA.axis.today;
let earliestRoleStart = Infinity;
let latestRoleEnd     = -Infinity;
DATA.roles.forEach(r => {
  const startVal = startOfMonth(r.start.year, r.start.month);
  if (startVal < earliestRoleStart) earliestRoleStart = startVal;
  const endVal = (r.end === "current")
    ? endOfMonth(today.year, today.month)
    : endOfMonth(r.end.year, r.end.month);
  if (endVal > latestRoleEnd) latestRoleEnd = endVal;
});

const chartStart     = Math.floor(earliestRoleStart);
const chartEnd       = Math.max(Math.ceil(latestRoleEnd), today.year + 1);
const chartSpanYears = chartEnd - chartStart;

// Lock total viewBox width; derive VB_PER_YEAR from career span.
CHART.vw          = CHART.TARGET_VB_TOTAL_WIDTH;
CHART.plotW       = CHART.vw - CHART.pad.left - CHART.pad.right;
CHART.VB_PER_YEAR = CHART.plotW / chartSpanYears;
CHART.plotH       = DATA.strata_bands.length * CHART.BAND_HEIGHT;
CHART.vh          = CHART.plotH + CHART.pad.top + CHART.pad.bottom;

// Per-role x-coordinate (bar AND its staircase arc-rect both use this):
// const x1 = CHART.pad.left + (startOfMonth(r.start.year, r.start.month) - chartStart) * CHART.VB_PER_YEAR;
// const x2 = CHART.pad.left + ((r.end === "current" ? endOfMonth(today.year, today.month)
//                                                    : endOfMonth(r.end.year, r.end.month)) - chartStart) * CHART.VB_PER_YEAR;
```

**Anti-pattern (do NOT do):** constant `VB_PER_YEAR: 80` gives every chart a different viewBox aspect ratio and produces inconsistent rendered band heights. Empirically, 8-year careers rendered bands at ~37 px while 13-year careers rendered at ~24 px. The lock-vw-derive-`VB_PER_YEAR` fix above eliminates this.

**Anti-pattern (do NOT do) - asymmetric end-date convention:** computing `endVal` with `(month - 1) / 12`, the same formula as `startVal`, silently renders every bar and staircase arc-rect about one month short on its trailing edge. Two roles at the same company with a genuinely seamless promotion (role A ends 2020-06, role B starts 2020-07) then render with a visible ~1-month dead zone between them, and every bar's rendered width quietly undercounts the JSON's own `duration_months` by one month. Always use `endOfMonth` (month, not month-1) for end dates and "current." See §5.5 for the staircase-specific symptom this caused.

**Preserve aspect ratio: keep `meet`.** Continue using `preserveAspectRatio: xMidYMid meet`. The locked-viewBox-width fix achieves vertical consistency WITHOUT needing `preserveAspectRatio: none`, which would distort grid circles, text glyphs, and other shapes inside the SVG.

### 5.3 Strata bands (Y-axis)

- Y-axis spans from the **lowest rank used by any on-chart role** to **max(peak_rank + 1, highest_band_used + 1)**.
- Always include one empty band above the peak for visual breathing room.
- Pass the strata bands list as `DATA.strata_bands` - an array of `{ code, name, rank }` entries ordered low-to-high.

Each band renders as a thin horizontal lane in the chart with a dotted grid background. Empty bands (no roles at that rank but within the span range) still render and contribute to the y-axis hierarchy.

**Floor and ceiling (UPDATED 2026-08-09, framework v3.0):**

- The floor is whatever the lowest on-chart role's rank actually is - **including rank 0 (`P1`)**. Do not clamp, offset, or `Math.max(..., 1)` the floor. A candidate whose career starts in a title-gated intern/trainee role legitimately has a rank-0 band as the bottom of their chart.
- Because the floor can be 0, any band-index arithmetic must be written as `rank - floorRank`, never as `rank - 1`. A hardcoded `- 1` silently shifts every bar down one band on P1-containing charts and pushes a rank-0 bar off the bottom of the plot area entirely.
- The one-empty-band-above rule is **clamped at the ceiling**: `topRank = Math.min(12, Math.max(peak_rank + 1, highest_band_used + 1))`. For a C-Level candidate (peak rank 12) there is no rank 13 to render, so the chart tops out at the C-Level band with no breathing room above it. Do not synthesize a phantom band.
- There is no matching clamp at the bottom: the breathing-room band is only ever added above the peak, never below the floor, so a rank-0 floor needs no special handling beyond not clamping it.

### 5.4 Strata axis overlay

- Strata codes (P3, P4, M5, etc.) render as an HTML overlay `#strata-axis` absolutely positioned to the right of `.ladder-frame`, NOT inside the SVG.
- Labels left-aligned with 6px left margin.
- Font-size: `clamp(10px, 1.1vw, 13px)` - scales with viewport.
- SVG `pad.right` is 12 (no inline labels - labels live in the overlay column).
- `.ladder-wrap` has `padding-right: 36px` to reserve space for the overlay so bars never slide under the labels.
- **`C-Level` shortens to `C` (UPDATED 2026-08-23).** Every other code in the column is 2-3 characters; `C-Level` is 7 and is the one rank where `code` and `name` are identical, so it reads redundantly long next to `P6` or `M4`. Shorten it at the point the label text is assigned: `div.textContent = b.code === "C-Level" ? "C" : b.code;`. `DATA.strata_bands` itself, and the JSON's `strata.code`, keep the full `C-Level` string - this substitution is display-only.

This overlay pattern (rather than SVG-inline labels) makes the labels resolution-independent and easier to style with CSS.

**Alignment across the two coordinate systems (LOCKED 2026-08-09).** The labels are HTML in CSS-pixel space; the bars are SVG in a viewBox that is scaled to the container width by `width: 100%` + `preserveAspectRatio: xMidYMid meet`. Keeping the two aligned at every viewport width requires that the overlay track the *rendered* SVG, not the viewBox constants. Three rules, each corresponding to a way a real chart shipped misaligned:

1. **Do not set a pixel height on `#strata-axis`.** Let it stretch to the frame with CSS `top: 0; bottom: 0`; the frame contains only the SVG, so the overlay inherits the rendered SVG height. Assigning `axisEl.style.height = vh + "px"` pins the overlay to a constant viewBox-unit height while the rendered SVG shrinks with width - the two diverge and every label drifts, mildly at the reference width and severely on narrow viewports.
2. **Anchor labels to the band center as a percentage of `vh`, never with a literal-px term.** `top = ((pad.top + fromTop*BAND_HEIGHT + BAND_HEIGHT/2) / vh) * 100 + "%"`, combined with `transform: translateY(-50%)` on the label. A missing `+ BAND_HEIGHT/2` anchors to the band's top edge (labels half a band high); a `calc(% + 6px)` nudge does not scale with the SVG and produces width-dependent drift.
3. **Invert the band index the same way the bars do** (`fromTop = strata_bands.length - 1 - i`), since bands are stored low-to-high but SVG y grows downward. Inverting in one place and not the other mirrors the labels.

The diagnostic signature of a violation is *resize drift*: labels that sit on their bars at desktop width but slide off as the window narrows. Verify by screenshotting the chart at ~900px and ~480px and confirming each bar sits in the row its label names at both sizes.

### 5.5 Same-employer staircase

When roles share a `company` value, render a faint gray staircase behind the bars:

- **Grouping (LOCKED 2026-06-08):** group ALL roles by `company` across the full role list - use a `byCompany` Map keyed by `r.company`, not chronological adjacency. Any company with 2+ roles emits one arc, regardless of whether other-company roles sit between them in start-date order. (An earlier version of this spec grouped by walking roles in start-date order and chaining consecutive same-company entries; that approach silently broke the arc whenever a side gig at a different company ran concurrently with the main employer. Group-by-company fixes that.)
- ONE rect per role in the arc
- Each rect spans the role's date range horizontally, using the exact same `startOfMonth`/`endOfMonth` x-coordinates as that role's own bar (§5.2) - this is what keeps the staircase and the bars in lockstep
- Each rect extends from JUST BELOW its band down to the chart bottom
- Together the rects form a continuous staircase under all bars, no gaps, no rect overlapping any bar
- Fill: `var(--ink-3)` at opacity 0.10
- `pointer-events: none` so it doesn't block bar interactions
- Class: `.same-employer-arc-block`
- Renders BEFORE bars so bars sit on top

**Resolved - the gap issue.** Consecutive same-company rects used to show a visible ~1-month notch even for a genuinely seamless promotion, making one continuous employer stint read as two separate ones. Root cause: the x-coordinate formula for an end date reused the "start of month" convention meant for start dates (see §5.2's anti-pattern note), so every rect was quietly drawn about a month short on its trailing edge - the same bug affected the bars themselves, just less visibly since a promotion already moves them to a different band. Fixed by giving end dates their own `endOfMonth` conversion: a role ending in month M now renders through the exact x-coordinate where a role starting in month M+1 begins, so two seamless same-company rects abut with zero gap.

### 5.6 Lane-splitting for concurrent same-rank roles

When two roles at the same `strata.rank` overlap in time:

- Compute per-role `laneCount` = max number of roles at the same rank whose time window overlaps with THIS role's own window.
- Bars at `laneCount = 1` (no overlap with anything at their rank) render at FULL band height.
- Bars with overlap split the band height proportionally.
- Touching at a month boundary does NOT count as overlap (e.g. role A ends 2024-03 and role B starts 2024-03 → both render at full height).

A role does not lose full height just because OTHER roles at the same rank overlap each other elsewhere - only that role's own overlap matters.

This overlap check is independent of the §5.2/§5.5 end-date fix: it compares month/year tuples directly (a discrete "does month M appear in both ranges" test), not rendered x-coordinates, so the `endOfMonth` change does not alter which roles count as touching vs. overlapping.

### 5.7 Bar encoding (UPDATED 2026-07-19, spec v1.2)

**Default: solid dominant-family-color bars.** Each bar renders as a single solid rect in the color of the role's dominant `family_tags` entry (highest weight; first-listed wins on exact tie). The weighted family split is NOT drawn on the bar - it's shown only in the hover tooltip (§5.9), which lists every `family_tags` entry with its weight as a percentage.

- Single-sentence roles (`role.single_sentence === true`) render solid in the dominant color - no special case needed, this is now the universal behavior.
- Estimated-date bars (`role.is_estimated === true`) still get opacity 0.55 plus the diagonal `#estimated-hatch` overlay on top of the solid fill.
- Legend pills and pill-click filtering key off the dominant family only (§5.10) - unaffected by this change.

**Legitimate alternate: weight-proportional horizontal stripes.** Spec v1.0/1.1 rendered multi-family roles (`family_tags.length > 1`) as stacked horizontal stripes sized by weight (dominant on top), with a thin `var(--paper)` 0.5px outline around the bar. This remains a valid style a user may request - implement by sorting `family_tags` descending by weight and stacking proportional-height rects (`stripeH = barH * fam.weight`) instead of drawing one solid rect. Tooltip and legend logic are identical either way.

### 5.8 Sphere color palette

Assign sphere colors by global rank - largest sphere (most months) gets rank-1 green, second gets rank-2 fuchsia, etc. Read sphere rankings from `aggregates.professional_spheres_ranked_by_dominant`.

| Rank | Color | Hex | Use |
|---|---|---|---|
| 1 | green | `#75a426` | Dominant sphere |
| 2 | fuchsia | `#cd1a8c` | Second sphere |
| 3 | teal | `#32c6c6` | Third |
| 4 | orange | `#e29c22` | Fourth |
| 5 | blue-gray | `#206a8b` | Fifth |
| 6 | red | `#cf1515` | Sixth |
| 7 | blue | `#4f5dd1` | Seventh |
| 8+ | gray | `#8f8c80` | Beyond |

### 5.9 Tooltip

- Container: `min-width: 240px; max-width: 296px`.
- Layout (vertical):
  - Header: dates 8.5px Fraunces 600 dark / title 13px 700 / company 11px 500
  - "Responsibilities by Professional Sphere" label (or singular "Professional sphere" for single-sentence roles)
  - Per-sphere stripes showing weight as a colored bar with family name + percentage
- No role-type pill, no industry footer.
- Tooltip is a direct child of `.chart-card`, positioned relative to that card.
- Hides on bar click (right before scroll-to-article triggers).

### 5.10 Legend

- Horizontal pill row centered below the chart.
- Each pill: 10×10px swatch + sphere name (11px Fraunces) + duration "Yy Mm" (10px ink-3 tabular).
- Container: `display: flex; flex-wrap: wrap; justify-content: center; gap: 6px 16px`; padding `0 5.83% 0 5%` matching SVG plot edges.
- Click pill → toggle dim non-matching bars (filter by dominant family).
- Aggregates spheres by **dominant family only** - secondary-weight stripes on bars do NOT add legend pills.

### 5.11 Interactivity

- **Chart card** is sticky (`position: sticky; top: 0; z-index: 20`).
- **Bar click** → smooth `window.scrollTo` to the matching `<article id="role_X">` (offset = top − sticky height − 24px). Target article pulses ~2.2s amber wash via `.role-highlight` class + `role-pulse` keyframes.
- **Tooltip** appears on bar hover; hides on bar click (right before scroll-to-article).
- **Legend pill click** → toggle dim non-matching bars by dominant family.

---

## 6. Typography

- Serif for display text (name, role titles, tenure value): Fraunces (Google Fonts)
- Sans for body text and bullets: Inter (Google Fonts)
- Tabular numerics for dates and durations

Include the Google Fonts CSS in the HTML `<head>`. Both families are free under SIL Open Font License.

---

## 7. Output

- Single `.html` file, self-contained
- No external runtime dependencies except Google Fonts CDN (`fonts.googleapis.com`)
- All CSS inline in `<style>`, all JS inline in `<script>`, all SVG generated by JS at runtime
- Works offline once cached

---

## 8. Anti-patterns (do NOT do)

- **Constant pixels-per-year scaling**: produces inconsistent band heights across candidates. Use locked-viewBox-width instead (see §5.2).
- **`preserveAspectRatio: none`** on the SVG: distorts shapes inside (text glyphs, circles, dotted grids). The locked-viewBox-width fix achieves vertical consistency while preserving aspect ratio properly.
- **Horizontal scrolling**: rejected. Fit-to-screen is the design. Long careers compress; short careers stretch.
- **Manually adding the "AI synthesis" label inside the paragraph**: the CSS pseudo-element handles it. Manual addition duplicates the label.
- **Rendering Languages, Top Skills, Personal Characteristics, etc. by default**: section conservatism rule. Only render on explicit request.
- **Paraphrasing or rewording bullets**: bullets are verbatim from the candidate.
- **Rendering education dates**: hard rule, no exceptions.
- **Adding composed status to the hero** (relocation preference, headline, objective): hero rule is strict.
- **Putting the tooltip inside `.ladder-wrap`**: it must be a direct child of `.chart-card` for positioning math to work.
- **Inferring a multi-family weight breakdown for a single-sentence role**: not enough data; render solid.
- **Setting a pixel height on `#strata-axis`** (e.g. `axisEl.style.height = vh + "px"`): pins the label overlay to viewBox units while the rendered SVG scales with width, so the labels drift off the bars - worse as the window narrows. Let CSS `top:0; bottom:0` size it. See §5.4.
- **A literal-px term in a strata label's `top`** (e.g. `calc(${pct}% + 6px)`): the px part doesn't scale with the SVG, causing width-dependent misalignment. Use a pure `%` of the band center plus `translateY(-50%)`. See §5.4.
- **Anchoring strata labels to the band top edge instead of the center**: omit the `+ BAND_HEIGHT/2` and every label sits half a band too high.

---

## 9. Version & contract

- Spec version: 1.6
- JSON schema version this targets: `1.0`
- Leveling framework version this targets: `3.0` (13 levels, ranks 0-12)
- Backward-compatible JSON additions (schema v1.1 with new optional fields) should be ignored gracefully by the renderer.
- Breaking schema changes (schema v2.0) require synchronized renderer updates.

### Changelog

- **1.6 (2026-08-23):** Two fixes from a real-world test parse (a CTO candidate with a peak C-Level role and a boomerang return to a former employer). (1) Tenure header (§3): the locked `Peak job level · CODE Name` wording pattern renders as the visibly duplicated `C-Level C-Level` for any C-Level candidate, since `code` and `name` are the identical string at that rank - added the one-line exception to print `C-Level` just once. (2) Company name rendering (§4.6): added a rendering rule for boomerang re-engagements (a candidate returning to a former employer years later, in a different role, with other employers in between) - render a small italic note under the company name on the more recent stint, matching `company_history_note`'s treatment, since the same-employer staircase (§5.5) otherwise draws what looks like one continuous tenure. See `reference/parsing.md`'s companion edge case for how Phase 1 flags this.
- **1.5 (2026-08-23):** The axis-overlay renderer (§5.4) never actually implemented the display-only shortening the spec already permitted for `C-Level` (§ Strata rank reference) - `div.textContent = b.code` printed the full 7-character string, which stands out against the 2-3 character codes on every other row. Added the concrete substitution (`b.code === "C-Level" ? "C" : b.code`) at the point the label text is set, in both this doc and `reference/visualization.md`'s canonical overlay block. The underlying data (`DATA.strata_bands`, `strata.code` in the JSON) is unchanged and must stay `C-Level`.
- **1.4 (2026-08-09):** Locked the strata axis-overlay alignment rules (§5.4) after a shipped chart rendered its Y-axis labels misaligned with the bars. Root cause: the overlay was given a pixel height in viewBox units (`axisEl.style.height = vh + "px"`) while the SVG scales to the container width, plus labels were anchored to the band top edge with a literal `+6px` nudge. All three are now called out as anti-patterns; the fix positions labels at the band center as a pure percentage of `vh` with `translateY(-50%)` and lets CSS `top:0; bottom:0` size the overlay. Added a resize-drift verification step.
- **1.3 (2026-08-09):** Aligned the rendering spec with leveling-framework v3.0. The rank reference table was still a 12-level ladder starting at P2/rank 1 and omitted `P1 Entry Professional` (rank 0) entirely, so a parsed P1 role had no defined rendering. Added the P1 row, documented the 0-12 rank range, and added explicit floor/ceiling rules to §5.3: never clamp the floor to 1, compute band indices as `rank - floorRank`, and clamp the breathing-room band at rank 12. Also corrected the top-level code from `C` to `C-Level` and the E7/E8 names to their canonical framework strings.
- **1.2 (2026-07-19):** Default bar encoding changed from weight-proportional stripes to solid dominant-family-color (§5.7); the striped style remains a documented, legitimate alternate on request. Added page density & dividers guidance (§3): centered hero, dividers only under Experience/Education/Tech Stack section headers, centered/tight tenure header with a fixed wording pattern.
- **1.1 (2026-07-18):** Fixed the parked same-employer staircase gap. End dates now use `endOfMonth` (month, not month-1) instead of reusing the start-date convention - see §5.2 and §5.5. Also reconciled §5.5's arc-detection description with the already-locked (2026-06-08) group-by-company logic; the spec had drifted out of sync with the SKILL.md on this point.
- **1.0:** Original spec.
