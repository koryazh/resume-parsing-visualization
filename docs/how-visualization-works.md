# How a Resume Becomes a Career-Ladder Visualization

A narrative walkthrough of the design principles and rules behind the career-ladder visualization. Aimed at readers who want to understand what they're looking at when they open one of these HTMLs - hiring managers reviewing candidates, recruiters comparing pools, anyone opening a rendered file for the first time.

This document sits alongside two others:
- `SKILL.md` - instructions for Claude on how to produce the visualization
- `career-ladder-visualization-spec.md` - the technical spec a developer would use to replicate the chart outside the skill system

Neither of those is designed to *read* the output. This document is.

---

## What you're looking at

The visualization has two co-equal halves stacked vertically on one page.

**On top**: an interactive infographic - the career ladder itself. This is where the *shape* of a candidate's career becomes visible: how long each role lasted, at what career level, in which professional sphere, and how those roles connect to each other.

**Below**: the full resume content as prose - hero (name + contacts), reverse-chronological experience with all bullets verbatim, education, optional sections. The textual half is the resume you'd get if you never saw the chart.

The two halves are linked: click a bar in the chart, and the page scrolls to the matching role's text section and highlights it briefly in amber. Hover a bar and a tooltip shows the role's dates, title, employer, and sphere breakdown. The chart card is sticky - as you scroll through the textual half, the chart stays visible at the top so you can jump back and forth.

This is intentional. The chart doesn't replace the resume - it navigates it.

---

## The two axes: what the chart measures

**Horizontal (X-axis) is time.** Each year of the candidate's career gets a slice of the chart. The leftmost edge is roughly the earliest role they've included; the rightmost edge is next year, so you can see whether their current role is ongoing and how long it's been. Year labels tick along the axis.

The whole career fits on one screen. No horizontal scrolling. This is a deliberate design choice: a 30-year career compresses horizontally, a 5-year career stretches. In exchange, you can see the entire arc at a glance without dragging.

**Vertical (Y-axis) is career level.** The chart uses a 12-level strata framework running from **P2 Junior** at the bottom through **P6 Principal**, then the manager track **M3 Team Lead** through **M6 Senior Director**, then executive levels **E7 VP**, **E8 SVP**, and finally **C-Level** at the top (Executive Officers - CTO, CFO, CEO, etc.).

Each candidate's chart only shows the bands from their lowest role's level up to their peak plus one band of breathing room. So a candidate whose career runs P3 → P5 sees four bands (P3, P4, P5, P6) rather than the whole 12-level ladder. This keeps the chart focused and the bars readable.

The strata codes appear on the right side of the chart as a sticky overlay, not inside the SVG itself. This means the codes stay crisp at any zoom level and take up visual space outside the bar-drawing area.

---

## Bars: what each dimension represents

Each career role in the on-chart part of the resume becomes one horizontal bar.

**Where the bar starts and ends** = the role's start month and end month. So a role that ran from March 2019 to November 2022 becomes a bar that starts at the 2019 mark, three months in, and ends at November 2022. Simple.

**Which vertical band the bar sits in** = the role's career level. An HR Manager assessed at P4 Senior sits in the P4 band; an HR Manager assessed at P5 Lead sits in the P5 band. This is where reading the *shape* of a career becomes intuitive: a career that climbs from P3 to P5 shows an upward staircase; a career that stays at P4 shows a flat line; a lateral move to a different domain shows a bar at the same level but with a different color.

**Height of the bar** = full band height by default. If two roles at the same level overlap in time (a side gig at the same career level as the main role, for example), the bars split vertically and each renders at half height for the overlap period. This is called *lane-splitting* - more on it below.

**Color of the bar** = the professional sphere of the role. This is where the chart tells you *what kind of work* the person did, alongside the level and duration.

---

## Colors: professional spheres

Every role has a professional sphere - Human Resources & People Operations, Talent Acquisition & Recruitment, Education & Training, Engineering & Software, Hospitality, and so on. The taxonomy has 37 families total; a candidate's chart usually surfaces 1 to 5 of them.

**Colors are assigned per candidate**, not fixed globally. The candidate's largest sphere (measured by months where that family dominates the role) gets **green** and rank 1. Second-largest gets **fuchsia** and rank 2. Then teal, orange, blue-gray, red, blue, and gray beyond that. So on one candidate, green means HR; on another, green means Engineering; on a third, green means Education.

This trips readers up initially, but it's the right choice: the palette optimizes for *within-candidate* comparison (which sphere is bigger for this person?) rather than *cross-candidate* consistency (does every HR person look green?). If you're comparing several candidates, always read the legend under each chart.

**The legend** appears as a horizontal row of colored pills below the chart. Each pill shows the sphere's color swatch, its name, and the total months this candidate spent with that sphere as their dominant one. You can click a pill to dim all bars not dominated by that sphere - useful for isolating "which parts of this career were HR" versus "which parts were adjacent domains."

**Weight-proportional stripes.** When a role covered more than one professional sphere, the bar isn't solid - it's split into horizontal stripes proportional to how much of the role each sphere covered. A role that was 70% Education and 30% Talent Acquisition renders as a green stripe on top and a fuchsia stripe on the bottom, with the green taking up 70% of the bar's height.

This is how the chart surfaces work threads that don't dominate a role but still shape it. An HR Generalist who spent significant time on recruitment gets a fuchsia (HR) bar with a small blue-gray (TA) stripe - the recruitment work is visible even though it wasn't the majority.

**Estimated-date bars** - when a role's start or end date had to be inferred (usually from group brackets like "2018-2020" without month precision), the bar renders at reduced opacity with a diagonal hatch overlay. This signals to the reader: "this bar's boundaries are approximate, not exact."

**Single-sentence roles** - when a role's description is just one sentence in the source resume, the bar renders solid in the dominant sphere color, no stripes. There isn't enough data to infer a multi-sphere breakdown.

---

## The same-employer staircase

When a candidate stayed at one employer across multiple roles - a promotion within the same company, or a lateral move between teams - the chart shows a faint gray staircase beneath the affected bars.

Each role in the same-employer arc gets its own gray rectangle that extends from just below its band down to the bottom of the chart, spanning the role's date range. Stacked together, the rectangles form a staircase whose shape traces the candidate's tenure at that employer.

The staircase visualization is important for two reasons. **First**, it makes internal promotions immediately visible - if a candidate went from P4 to P5 while staying at the same company, the staircase steps up at the promotion month. **Second**, it distinguishes "changed roles by moving to a different company" from "changed roles by being promoted within the same company" - two career patterns that read very differently to hiring managers.

The grouping is by company name, not chronological order. If a side gig at a different company runs parallel to a main career stint at one employer, the side gig doesn't break the same-employer arc - it just sits alongside it visually. This handles candidates like people who taught part-time at one institution while working full-time somewhere else.

---

## Lane-splitting: concurrent roles

Some candidates had two or more roles running at the same time. A part-time teaching gig alongside a main HR job. A consulting side project during a full-time engineering role. A fitness instructor gig on top of a kindergarten teaching career.

When two roles share the same career level (both at P3, say) *and* overlap in time, the chart lane-splits: both bars render at half the normal band height so they can sit side-by-side within the same y-band without occluding each other.

Non-overlapping roles at the same level render at full height. So the visual signal is clean: a bar at half-height means *this role overlapped with another role at the same level at some point during its duration*.

Note that the half-height applies to the *entire* duration of both roles, not just the overlap window. This is a deliberate trade-off: the alternative (variable-height bars with sharp transitions where the overlap starts/ends) would create visually jarring shapes. Uniform half-height across each role's full duration is calmer and still communicates the concurrent-activity signal clearly.

Two roles at *different* levels that overlap don't lane-split at all - they sit in different bands and don't compete for space.

---

## What the textual half preserves

The chart is a summary. The textual half below it is the source material.

**Bullets are verbatim.** Every bullet under every role in the experience section is copied word-for-word from the source resume (or from LinkedIn, in the case of LinkedIn-augmented resumes, with the source noted). Nothing is paraphrased or reworded. This is a strict rule. It exists so the candidate's voice - how they chose to describe their own work - is preserved. The visualization interprets *level* and *sphere*, but the description is theirs.

**Long roles get an AI synthesis panel.** When a role has eight or more bullets, a short paragraph appears above the bullet list - a two-to-three-sentence summary of what the role covered, composed by Claude. This is the *only* prose in the experience section that isn't verbatim from the source. It's marked clearly with an "AI SYNTHESIS" label (rendered via CSS, so it's stylistically distinct from candidate-authored content). The intent is to help readers scan long roles quickly without discarding any of the source detail.

**Education has no dates.** The education section shows institution, degree, and field, but no graduation years or attendance dates. This is intentional - it protects candidates from age-based screening. Even if the source resume includes dates, they're not rendered here.

**The hero is strict.** The top of the page shows only: candidate name, contacts (phone / email / LinkedIn as available), location. No headlines, taglines, objectives, availability status, or self-descriptors. If the source resume has a two-line summary, it's captured in the underlying data but doesn't render on the page. This is a design choice to keep the reading experience focused: the candidate's career shape and content speak for themselves; overlaid tagline prose competes with them.

**Section conservatism.** Some resumes include sections for languages, top skills, personal characteristics, interests, driver's license, references. By default the visualization renders only Hero, Chart, Experience, and Education. Tech Stack and Honors appear conditionally when the source has meaningful content for them. Everything else is captured in the JSON but doesn't render on the page unless specifically requested. The intent is a page you can hand to a hiring manager without page-length inflation from optional sections.

---

## Data honesty and audit trail

The underlying JSON data is a fully-explicit record. Every level assignment has reasoning attached. Every family weight has a rationale. Every borderline call - a "Manager" title that turned out to be IC scope, a role whose level changed after a second reading of the bullets - records its revision history in a `data_quality` section.

This matters for two reasons. **First**, if a hiring manager questions why the chart placed someone at P4 rather than P5, the reasoning is available. Nothing is asserted without a paper trail back to the source resume's language and the framework's dimension definitions. **Second**, when new information comes in - a LinkedIn export that adds roles the resume didn't include, an interview conversation that clarifies scope - the data can be revised without losing the earlier context. The audit trail preserves the full sequence of calls.

Off-chart roles are captured with the same fidelity as on-chart ones. If the user chose to keep pre-career work (early hospitality jobs, entry-level admin roles in a different sphere) out of the chart to focus on the main career arc, the JSON still records those roles with full level assignments - they just don't render as bars. If the same resume is later re-rendered in a "maximal history" view where all roles are on-chart, the level assignments are already made.

---

## What the visualization reveals

The chart makes several patterns visible that are hard to see when reading a resume as prose:

- **Career shape**. Upward trajectory, sideways moves, stall periods, promotion cliffs. The shape of a candidate's career becomes something you can read at a glance.
- **Career level trajectory over time**. Where they've plateaued, where they've stepped up, where they've made a lateral move to a different domain but at the same level.
- **Sphere mix**. Whether a candidate is single-sphere (all HR, all Engineering) or multi-sphere; whether a "recruitment thread" runs through an HR career; whether teaching or program management appears as a side thread; whether the candidate's self-described identity matches the months-based reality.
- **Tenure patterns**. Long stays at one employer versus job-hopping. Concentration of roles in a certain company versus fragmentation across many.
- **Same-employer promotions**. Internal advancement versus lateral moves that required changing companies.
- **Concurrent activities**. Side gigs, parallel work, teaching alongside main employment.
- **Recent activity**. Whether the current role is ongoing or ended; whether there's a gap; how long the gap has been.

## What the visualization hides

Equally important:

- **Reasons behind role changes**. The chart shows *that* a candidate moved from company A to company B, not *why*. That context lives in the textual half.
- **Individual accomplishments**. The chart shows scope by level, but doesn't surface specific wins, projects, or metrics. Those are in the bullets below.
- **Cultural fit, communication style, ambition**. These aren't in a resume at all - they emerge in interviews.
- **Compensation, geography preferences, availability**. Not on the chart. Some are in the hero; most require conversation.
- **Titles below the strata level**. A candidate whose resume shows "Senior HR Business Partner" at P5 will appear at P5, but the "Senior" adjective in the title itself isn't visually distinct - the strata band is doing that work already.

The chart is a lens, not a decision tool. It's designed to make the first 30 seconds of resume review much richer, so the deep-review time (reading bullets, checking dates, forming interview questions) is spent on the right candidates.

---

## Design principles in one page

The rules above are numerous, but they follow from a small set of principles:

1. **Fit-to-screen** - the whole career must be visible without scrolling. Compare across candidates by opening two tabs, not by squinting at partial views.
2. **Comparability across candidates** - band heights are locked to a consistent pixel size regardless of career length, so a P5 band on one candidate looks the same as a P5 band on another. Only the horizontal density varies.
3. **Data honesty** - nothing invented, nothing paraphrased, nothing without an audit trail. If a level assignment is borderline, the reasoning is captured. If a date is estimated, the bar shows that visually.
4. **Candidate voice preserved** - bullets verbatim, hero strict, education without dates. The candidate wrote their resume; the visualization interprets structure, not content.
5. **Interactivity connects the two halves** - the chart summarizes, the text preserves the source. Click connects them. Neither half is redundant with the other.
6. **Section conservatism** - render what the reader needs; keep the page focused. Optional sections stay optional.
7. **Age-screening protection** - no education dates, ever. The candidate's academic timeline is not the chart's business.
8. **Per-candidate palette** - colors optimize for within-chart clarity, not cross-chart consistency. Read the legend.

These principles are why the visualization looks the way it does. Every rule above traces back to at least one of them.

---

## Reading a career-ladder chart in practice

If you're reviewing a chart for the first time:

1. **Start with the tenure header** at the top - the "N years N months of total tenure" number gives you the baseline for how much career you're looking at.
2. **Trace the trajectory left-to-right**. Where does it start? Where does it end? What's the shape - upward, flat, zigzag, staircase within a company?
3. **Note the peak strata band**. What's the highest level this candidate has reached? Is it the current role, or was it reached earlier?
4. **Read the legend under the chart**. What professional spheres are here, and in what ratios? Any surprises versus what you'd expect from the candidate's stated identity?
5. **Look for staircases** - same-employer arcs with promotions. Internal advancement is often a stronger signal than external job-hopping.
6. **Look for stripes** - multi-sphere bars indicate roles that straddled domains. Might explain gaps or lateral moves.
7. **Look for lane-splits** - parallel activities. Might indicate a side gig, teaching, consulting, or a life-stage transition.
8. **Click a bar of interest** to jump to the textual details for that role. Read the bullets. Note the AI synthesis paragraph if present.
9. **Return to the chart** - the sticky card stays visible - and continue exploring.

The goal is to spend ~30 seconds getting the overall shape and ~5 minutes on the roles that actually matter for the specific hire you're making. The chart tells you where to focus.
