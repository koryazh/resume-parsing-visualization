## Phase 2 of 2: visualization

This is the visualization phase of the unified `resume-parsing-visualization` skill. Phase 1 (`reference/parsing.md`) produces `structured.json`; this phase consumes it and produces `career-ladder.html`. Read this file in full before starting a render.

The JSON schema (v1.0) is the contract. This phase reads specific field paths from the JSON; parsing changes that break those paths break the visualization. See the `Schema (v1.0)` section of `reference/parsing.md` for the input contract.

Also see the companion documents in this skill's `docs/` folder:
- `visualization-technical-spec.md` - the standalone technical spec, portable to environments outside this skill system
- `how-visualization-works.md` - reader-facing narrative for hiring managers opening the HTML for the first time

## Required reading before rendering

Before starting a new render, read this file (`reference/visualization.md`) fully. This skill intentionally ships with no candidate example files (per its portability rule: no candidate data bundled). If a similar candidate shape has been rendered before earlier in this conversation or session (single-sphere HR career, R&D long career, multi-sphere with side gigs), look at that prior render's HTML as a template. Otherwise, build directly from the rules in this document: solid dominant-family-color bars (see Bar encoding below), centered hero, dividers only under Experience/Education/Tech Stack section headers, and a centered/tight two-line tenure header.

## The rendering workflow

1. Read the `structured.json`. Confirm `$schema_version: "1.0"` and `taxonomy_source: "job-families-and-industries.json v2.0"` (or later).
2. Pick the closest structural template (see `visualization-technical-spec.md` for shape patterns). Copy that HTML as a starting point.
3. Replace candidate-specific data:
   - Hero (name, contacts, location)
   - Tenure header
   - Experience articles (reverse-chronological, verbatim bullets, AI synthesis panel for 8+ bullets)
   - Education, honors, tech stack (per section conservatism)
   - DATA block in the script tag (axis, strata_bands, sphere_palette, roles, aggregates)
4. Verify every LOCKED rule below is honored.
5. Sanity-check braces/parens balance in the JS. Sanity-check all articles have matching bars in DATA.roles for on-chart roles.
6. Deliver.

## Content presentation rules (LOCKED)

These rules govern the textual half. They exist to preserve candidate voice and protect against unintended screening/bias.

1. **Bullets are rendered verbatim** from the JSON's `narrative_bullets`. Never paraphrase, reword, combine, or truncate. Preserve the exact character sequence including any typos, "etc.", and inline formatting.
2. **AI synthesis panel** for roles with 8+ bullets: render a 2-3 sentence composed summary above the bullet list in a gray-bordered panel. The "AI SYNTHESIS" label is rendered via CSS `::before` pseudo-element on `.role-summary` - **do NOT add a `<span>` containing the label text inside the paragraph** (that produces a duplicate label).
3. **Hero rule (STRICT)**: Hero block contains ONLY:
   - Candidate's name
   - Contacts row - phone, email, LinkedIn (only those that exist in JSON)
   - Location line - verbatim from JSON
   
   Append `work_authorization` ONLY if populated. NEVER append: relocation status, remote/hybrid preferences, headline, objective, tagline, summary.
   **Layout (UPDATED 2026-07-19)**: hero is center-aligned (name, contacts row, location line all `text-align: center`).

3b. **Page density & dividers (LOCKED 2026-07-19)**: Keep vertical rhythm tight and dividers sparse.
   - Only these three section headers get a `border-bottom` divider: **Experience**, **Education**, **Tech Stack** (i.e. the `.section-title` elements). No other divider lines anywhere else on the page.
   - Do NOT render a divider between individual role articles in Experience - roles are separated by padding/whitespace only, not a rule line.
   - Do NOT render a divider between the hero and the chart card, or between the chart card and the Experience section.
   - Hero padding: tight top/bottom (~20px top, ~12px bottom is the reference value); name-to-contacts gap ~6px.
   - Tenure header (the stats row above the chart): center-aligned, both stat lines rendered at the SAME font size (12px reference value) with bold applied only to the actual numbers/values via `<b>`, not to the whole line. Wording pattern: `Career path span <b>X years Y months</b> · <b>N roles</b> · <b>M employers</b>` on one line, `Peak job level · <b>CODE Name</b>` on the next.
   - Keep the gap between the tenure header and the chart itself very small (near-zero bottom padding on the tenure header) so the stats read as clearly belonging to the chart directly below them, not as a separate block.
4. **Education dates are NEVER rendered**, even if they appear in the JSON. Protects against age-based screening.
5. **Section conservatism**: render by default only Hero, Chart Card, Experience, Education. Conditional sections: Tech Stack (if JSON has data AND candidate is tech-adjacent), Honors (if JSON has data). NEVER render by default: Languages, Top Skills, Personal Characteristics, Interests, Driver's License, References - only on explicit user request.
6. **Company name rendering**:
   - `company_history_note` (mid-employment renames like "SoftwareHaus → ThePayPortal") → small italic line under the company name on the most-recent role at that employer
   - `title_history_note` (consolidated multi-title entries) → small italic line
7. **Off-chart roles** (`render_policy.on_chart === false` AND `in_experience_text === true`): render normally in Experience section, exclude from chart DATA.roles.
8. **Internships** (optional array): render as a compact sub-block within Experience, NOT on the chart.

## Visual grammar (LOCKED)

### Fit-to-screen
- X-axis spans exactly the on-chart career (earliest role start floor'd, latest end ceil'd, min today.year+1)
- Whole career fits on one screen - **no horizontal scrolling**
- SVG uses `width: 100%; height: auto` with `viewBox`

### Locked viewBox total width → constant rendered band height
The chart MUST render each strata band at the same CSS-pixel height regardless of how many years the candidate's career spans.

**Canonical values:**
- `TARGET_VB_TOTAL_WIDTH: 828` - chosen to match rendered container width (chart-card 880 max-width minus 8×2 padding minus 36 right reserve)
- `BAND_HEIGHT: 25` viewBox units → bands render at ~25 CSS px on every candidate
- `preserveAspectRatio: xMidYMid meet` - kept because locked-viewBox-width achieves vertical consistency without needing `preserveAspectRatio: none`

```javascript
CHART.vw = CHART.TARGET_VB_TOTAL_WIDTH;      // constant
CHART.plotW = CHART.vw - CHART.pad.left - CHART.pad.right;
CHART.VB_PER_YEAR = CHART.plotW / chartSpanYears;  // derived, varies per candidate
CHART.plotH = DATA.strata_bands.length * CHART.BAND_HEIGHT;
CHART.vh = CHART.plotH + CHART.pad.top + CHART.pad.bottom;
```

**Anti-pattern (do NOT do)**: constant `VB_PER_YEAR: 80` produces inconsistent rendered band heights across candidates because the SVG scale factor varies with viewBox aspect ratio.

**Date → x-coordinate helpers (FIXED 2026-07-18 - use these exactly, everywhere a role's dates become an x-coordinate):**

```javascript
const startOfMonth = (year, month) => year + (month - 1) / 12;   // start dates
const endOfMonth   = (year, month) => year + month / 12;          // end dates + "current"
```

Start dates and end dates are NOT symmetric. A role starting in month M begins at the *start* of M (`startOfMonth`). A role ending in month M runs through the *end* of M, which is the same point as the start of month M+1 (`endOfMonth`). Use `startOfMonth` for every `start_date`/`start.month`, and `endOfMonth` for every `end_date`/`end.month` and for "current" (using today's month) - for bar x1/x2, the same-employer staircase arc-rect x1/x2 (see below), and the `chartStart`/`chartEnd` bounds above. Reusing `startOfMonth` for end dates is the anti-pattern that caused the staircase-gap bug: it silently renders every bar about a month short on its trailing edge, so a role ending 2020-06 and the next role at the same company starting 2020-07 - a seamless promotion - render with a visible gap between them instead of touching. `endOfMonth` closes that gap and also stops under-rendering every bar's width relative to the JSON's own `duration_months`.

### Strata bands (Y-axis)
- Y-axis spans from the **lowest rank used by any on-chart role** to **max(peak_rank + 1, highest_band_used + 1)**
- Always include one empty band above the peak for visual breathing room
- Pass strata bands as `DATA.strata_bands` - array of `{ code, name, rank }` ordered low-to-high

### Strata axis overlay
- Strata codes (P3, P4, M5, etc.) render as an HTML overlay `#strata-axis` absolutely positioned to the right of `.ladder-frame`, NOT inside the SVG
- Labels left-aligned, 6px left margin
- Font-size: `clamp(10px, 1.1vw, 13px)` - scales with viewport
- SVG `pad.right = 12` (no inline labels)
- `.ladder-wrap` has `padding-right: 36px` to reserve space for the overlay

### Same-employer staircase
- When 2+ roles share a `company` value → render faint gray staircase behind the bars
- **Grouping logic (LOCKED 2026-06-08)**: group roles by company across the full role list, NOT by chronological adjacency. Use a `byCompany` Map keyed by `r.company`. Any company with 2+ roles emits one arc, regardless of whether other-company roles sit between them in start-date order.
- **Why group-by-company, not chronological-adjacency**: when a side gig at a different company runs parallel to a main career stint, the chronological-adjacency algorithm resets the arc when it hits the side gig - losing the same-employer connection. Group-by-company correctly groups all roles at the same employer as one arc; concurrent different-company roles render standalone.
- ONE rect PER ROLE in the arc, spanning that role's date range horizontally - using the exact same `startOfMonth`/`endOfMonth` x-coordinates as that role's own bar, from JUST BELOW its band down to the chart bottom
- Together the rects form a continuous staircase under all bars at the same employer
- Fill: `var(--ink-3)`, opacity 0.10, `pointer-events: none`
- Class: `.same-employer-arc-block`
- Renders BEFORE bars so bars sit on top
- **Visual effect**: internal promotions (P4 Senior → P5 Lead at the same company) show as a staircase step UP at the promotion month - strong visual signal of internal advancement
- **Fixed 2026-07-18**: consecutive same-company rects used to show a ~1-month gap even for a genuinely seamless promotion, because the end-date x-coordinate reused the start-date's "start of month" convention instead of `endOfMonth`. If you ever see a same-employer staircase read as two disconnected stints, check that both the bar-drawing code and the arc-rect code are calling the shared `endOfMonth` helper above - not recomputing the date conversion inline.

**Canonical JS block:**
```javascript
const arcs = [];
const byCompany = new Map();
sorted.forEach(r => {
  if (!byCompany.has(r.company)) byCompany.set(r.company, []);
  byCompany.get(r.company).push(r);
});
byCompany.forEach(roles => {
  if (roles.length >= 2) arcs.push(roles);
});
```

### Lane-splitting for concurrent same-rank roles
- Per-role `laneCount` = max number of roles at the same rank whose time window overlaps with THIS role's own time window
- Non-overlapping roles render at FULL band height (`laneCount = 1`), even when other roles at the same rank overlap each other elsewhere on the timeline
- Touching at a month boundary does NOT count as overlap (e.g. role A ends 2024-03 and role B starts 2024-03 → both render at full height)

**When does this trigger?** Two patterns:
- **Side gig at the same rank as a main role**: e.g. a P4 Lecturer running parallel to a P4 HR Generalist for 11 overlap-months. Both bars render at half-height for their FULL durations (any overlap within the role's window triggers half-height across the whole role).
- **Concurrent side gigs in different spheres**: e.g. a P3 Fitness Instructor running parallel to a P3 Kindergarten Teacher. Both at P3 → both render at half-height.

**Strata changes cascade**: when a strata revision moves a role into/out of an overlapping rank, lane-splitting kicks in or releases. Always re-check what's at each rank after a strata revision.

**Visual cost**: a role gets half-height for its ENTIRE duration if any overlap exists at its rank, even if the overlap is brief. This is the spec; the alternative (per-month height adjustment) would produce visually jarring bars. Accept the cost; the lane-split signals "concurrent activity" clearly enough.

### Bar encoding (UPDATED 2026-07-19)

**Default: solid dominant-family-color bars.** Each on-chart bar renders as a single solid rectangle in the color of the role's dominant `family_tags` entry (highest weight; first-listed wins on exact tie). The full weighted family split for that role is NOT shown on the bar itself - it lives only in the hover tooltip (see Tooltip section below), which lists every family_tags entry with its weight as a percentage.

- **Single-sentence roles** (`role.single_sentence === true`) render solid in the dominant color - same as every other role now, since solid is the baseline. No special-casing needed.
- **Estimated-date bars** (`role.is_estimated === true`) still get opacity 0.55 plus a diagonal hatch overlay defined as `<pattern id="estimated-hatch">`, applied on top of the solid fill.
- Legend pills and pill-click filtering key off the dominant family only (unchanged from before - see Legend section).

**Legitimate alternate: weight-proportional horizontal stripes.** An earlier version of this skill rendered multi-family roles (`family_tags.length > 1`) as stacked horizontal stripes sized by weight, dominant stripe on top, with a thin `var(--paper)` 0.5px outline around the whole bar to set it off from neighbors. Single-family and single-sentence roles rendered solid either way. This remains a legitimate style the user has asked for before and may ask for again - if requested, revert the bar-drawing code to sort `family_tags` descending by weight and stack proportional-height rects (`stripeH = barH * fam.weight`) instead of drawing one solid rect from `tags[0]`. Keep the tooltip and legend logic unchanged either way; they don't depend on which bar style is active.

### Sphere color palette

The sphere palette assigns a color to each professional family present in the candidate's roles. Two distinct concerns:

**1. Ranking → color assignment (for the dominant spheres)**

Read sphere rankings from `aggregates.professional_spheres_ranked_by_dominant` in the JSON. This array is pre-ranked by months-where-dominant (largest first). Map rank → color from this fixed palette:

| Rank | Color | Hex |
|---|---|---|
| 1 | green | `#75a426` |
| 2 | fuchsia | `#cd1a8c` |
| 3 | teal | `#32c6c6` |
| 4 | orange | `#e29c22` |
| 5 | blue-gray | `#206a8b` |
| 6 | red | `#cf1515` |
| 7 | blue | `#4f5dd1` |
| 8+ | gray | `#8f8c80` |

**2. Secondary-weight families** (families that appear in some role's `family_tags` but aren't dominant in any role)

These families still need a palette entry - bars render multi-family roles as weight-proportional stripes, and every stripe needs a color. Assign secondary families to the next-available rank after the dominant spheres. They render as stripe color but do NOT appear in the legend.

Example palette structure in `DATA.sphere_palette`:

```javascript
sphere_palette: {
  "education_training":         { rank: 1, color: "#75a426", name: "Education & Training" },
  "human_resources":            { rank: 2, color: "#cd1a8c", name: "Human Resources & People Operations" },
  "personal_domestic_services": { rank: 3, color: "#32c6c6", name: "Personal & Domestic Services" },
  "hospitality_food_service":   { rank: 4, color: "#e29c22", name: "Hospitality & Food Service" },
  "talent_acquisition":         { rank: 5, color: "#206a8b", name: "Talent Acquisition & Recruitment" },
  "administrative_office":      { rank: 6, color: "#cf1515", name: "Administrative & Office Support" }
}
```

First 4 are dominant in 1+ roles (legend pills); ranks 5+ are secondary (no legend, just stripe color).

**Taxonomy note**: `human_resources` and `talent_acquisition` are siblings, not nested (unaffected by the v2.0 family-list restructuring). A candidate with both HR-dominant and TA-dominant roles gets TWO palette entries with distinct colors. A candidate with only HR-dominant roles (TA always secondary) gets `human_resources` as a ranked sphere and `talent_acquisition` as a secondary palette entry - visible as fuchsia stripes on bars but no legend pill.

### Tooltip
- Container: `min-width: 240px; max-width: 296px`
- Layout (vertical):
  - Header: dates 8.5px Fraunces 600 dark / title 13px 700 / company 11px 500
  - "Responsibilities by Professional Sphere" label (or singular "Professional sphere" for single-sentence roles)
  - Per-sphere stripes showing weight as a colored bar with family name + percentage
- No role-type pill, no industry footer
- Tooltip is a direct child of `.chart-card`, positioned relative to that card
- Hides on bar click (right before scroll-to-article triggers)

### Legend
- Horizontal pill row centered below the chart
- Each pill: 10×10px swatch + sphere name (11px Fraunces) + duration "Yy Mm" (10px ink-3 tabular)
- Container: `display: flex; flex-wrap: wrap; justify-content: center; gap: 6px 16px`
- Click pill → toggle dim non-matching bars (filter by dominant family)
- Aggregates spheres by **dominant family only** - secondary-weight stripes on bars do NOT add legend pills

### Interactivity
- **Chart card** is sticky (`position: sticky; top: 0; z-index: 20`)
- **Bar click** → smooth `window.scrollTo` to matching `<article id="role_X">` (offset = top − sticky height − 24px). Target article pulses ~2.2s amber wash via `.role-highlight` class
- **Tooltip** appears on bar hover; hides on bar click
- **Legend pill click** → toggle dim non-matching bars by dominant family

## Typography

- Serif for display text (name, role titles, tenure value): Fraunces (Google Fonts)
- Sans for body text and bullets: Inter (Google Fonts)
- Tabular numerics for dates and durations

## Output

- Single self-contained HTML file
- No external runtime dependencies except Google Fonts CDN
- All CSS inline in `<style>`, all JS inline in `<script>`, all SVG generated by JS at runtime
- Works offline once fonts are cached

## Contract dependency

This skill depends on the parsing phase's JSON schema v1.0. Read `reference/parsing.md`'s `Schema (v1.0)` section for the input contract. This skill fails loudly if required fields are missing (`roles[].strata`, `roles[].family_tags`, `aggregates.professional_spheres_ranked_by_dominant`, etc.).
