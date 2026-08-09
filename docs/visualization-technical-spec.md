# Career Ladder Visualization - Rendering Spec

A self-contained specification for building an interactive HTML career-ladder visualization from a structured resume JSON. This document covers the input contract (JSON schema), page-level content presentation rules, and chart-rendering rules (geometry, encoding, palette, interactivity).

The output is a single self-contained HTML file. No external runtime dependencies except Google Fonts. All chart drawing is inline SVG; all interactivity is plain JS; styling is plain CSS (no framework).

---

## 1. Overview

The page has two co-equal halves:

1. **Chart card** (top, sticky) - an interactive infographic showing the candidate's career progression as bars across two axes:
   - **X** = time (year)
   - **Y** = strata (career level: P2 Junior through C-Level)
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

### Strata rank reference (12-level ladder, low → high)

| Code | Name | Rank |
|---|---|---|
| P2 | Junior | 1 |
| P3 | Middle | 2 |
| P4 | Senior | 3 |
| P5 | Lead | 4 |
| P6 | Principal | 5 |
| M3 | Team Lead | 6 |
| M4 | Manager | 7 |
| M5 | Director | 8 |
| M6 | Senior Director | 9 |
| E7 | VP | 10 |
| E8 | SVP | 11 |
| C | C-Level | 12 |

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

- Y-axis spans from the **lowest rank used by any role** to **max(peak_rank + 1, highest_band_used + 1)**.
- Always include one empty band above the peak for visual breathing room.
- Pass the strata bands list as `DATA.strata_bands` - an array of `{ code, name, rank }` entries ordered low-to-high.

Each band renders as a thin horizontal lane in the chart with a dotted grid background. Empty bands (no roles at that rank but within the span range) still render and contribute to the y-axis hierarchy.

### 5.4 Strata axis overlay

- Strata codes (P3, P4, M5, etc.) render as an HTML overlay `#strata-axis` absolutely positioned to the right of `.ladder-frame`, NOT inside the SVG.
- Labels left-aligned with 6px left margin.
- Font-size: `clamp(10px, 1.1vw, 13px)` - scales with viewport.
- SVG `pad.right` is 12 (no inline labels - labels live in the overlay column).
- `.ladder-wrap` has `padding-right: 36px` to reserve space for the overlay so bars never slide under the labels.

This overlay pattern (rather than SVG-inline labels) makes the labels resolution-independent and easier to style with CSS.

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

---

## 9. Version & contract

- Spec version: 1.2
- JSON schema version this targets: `1.0`
- Backward-compatible JSON additions (schema v1.1 with new optional fields) should be ignored gracefully by the renderer.
- Breaking schema changes (schema v2.0) require synchronized renderer updates.

### Changelog

- **1.2 (2026-07-19):** Default bar encoding changed from weight-proportional stripes to solid dominant-family-color (§5.7); the striped style remains a documented, legitimate alternate on request. Added page density & dividers guidance (§3): centered hero, dividers only under Experience/Education/Tech Stack section headers, centered/tight tenure header with a fixed wording pattern.
- **1.1 (2026-07-18):** Fixed the parked same-employer staircase gap. End dates now use `endOfMonth` (month, not month-1) instead of reusing the start-date convention - see §5.2 and §5.5. Also reconciled §5.5's arc-detection description with the already-locked (2026-06-08) group-by-company logic; the spec had drifted out of sync with the SKILL.md on this point.
- **1.0:** Original spec.
