## Phase 2 of 2: visualization

This is the visualization phase. Phase 1 (`reference/parsing.md`) produces `structured.json`; this phase turns it into `career-ladder.html`.

**Since spec 2.0, you do not write HTML.** The page is `viewer/career-profile.html`, a finished renderer bundled with this skill that reads any conforming JSON and draws the chart in the browser. Rendering a candidate is one script run. Writing a page by hand instead is the single thing this phase forbids: every hand-written render before 2.0 re-implemented the same 600 lines and dropped a different rule each time (see the spec's 1.8 and 1.9 changelog entries, both of which are records of exactly that).

What still belongs to you: getting the JSON right, composing the two AI-synthesis texts, recording the user's rendering choices, and checking the result.

## The rendering workflow

1. **Validate.** `python3 scripts/validate_structured_json.py path/to/structured.json`
   Fix every ERROR. Read the WARNs: several of them (missing `career_synthesis`, 8+ bullets with no `role_synthesis`, a title-only role) describe content that will be quietly absent from the page rather than anything that looks broken.
2. **Confirm the composed text exists** (see "Composed text" below). The viewer never writes prose. If the JSON has no `career_synthesis`, the page has no full-career panel; if a role with 8+ bullets has no `role_synthesis`, that role has no AI SYNTHESIS panel.
3. **Record the user's rendering choices** in `render_options`, if they asked for any (see `reference/viewer-contract.md`). Never add one unprompted; section conservatism still applies.
4. **Build.** `python3 scripts/build_profile.py path/to/structured.json -o <Name>_career-ladder.html`
   The build re-runs the validator and refuses to write while any ERROR stands. It prints the counts the page header will show.
5. **Check the result.** Open the file if you can. Confirm the header's role and employer counts match the bars, the axis labels sit on their bars at a wide and a narrow window width, and the bullets read verbatim. The counts are computed by the viewer from the on-chart roles, so a mismatch means the JSON, not the renderer, is wrong.
6. **Deliver both files**: the HTML and the `structured.json` it was built from. The JSON is what a re-render, a later edit, or any other consumer needs.

**Entry point for a JSON that already exists** (user hands you one, or asks for a re-render after editing): start at step 1. Nothing about this phase needs the parsing rules or the resume PDF.

## When Python is not available

The build script is standard-library Python 3 and runs anywhere this skill's files are unpacked. If the environment genuinely cannot run it, do **not** fall back to writing a page by hand. Deliver the JSON together with `viewer/career-profile.html` and tell the user to open the viewer and drop the JSON onto it. The result is identical apart from being two files instead of one.

## Composed text (the only prose this phase produces)

Both fields are written during Phase 1 and simply carried by the JSON. If you are running Phase 2 alone on a JSON that lacks them, offer to compose them, and write them into the JSON before building rather than into the HTML afterwards.

| Field | Renders as | Rule |
|---|---|---|
| `candidate.career_synthesis` | Full-career panel between the hero and the chart, collapsed behind a "Show career synthesis" toggle | 3-4 sentences on the arc from first to current role, the shape of the transitions, and the spheres actually worked in |
| `roles[].role_synthesis` | Per-role AI SYNTHESIS panel above the bullets, for roles with **8 or more** bullets only | 2-3 sentences summarizing that role |

Every claim must be checkable against the JSON: no praise, no adjectives the bullets do not support, no invented metrics, and nothing that contradicts the leveling calls or the sphere ranking. These panels are labelled as AI synthesis on the page precisely so a reader can tell them from the candidate's own words; everything else on the page is verbatim.

## What the viewer already enforces

These were prose rules before 2.0, and each one was dropped by at least one hand-written render. They are now code. You do not need to re-check them, and you cannot change them per candidate:

- Verbatim bullets, rendered exactly as the JSON carries them.
- Hero shows only name, contacts (phone, email, LinkedIn), location and work authorization.
- Education never shows dates.
- Section conservatism: Experience and Education always; Tech Stack when there is data and the candidate is tech-adjacent; Honors when there is data; Languages, Top Skills, Interests and the rest only when `render_options.extra_sections` names them.
- Tenure header counts, career span, peak level, sphere ranking and legend months are computed from the on-chart roles, so they can never contradict the chart.
- Chart geometry: locked viewBox width (828) and band height (25), fit-to-screen timeline, rank range 0-12 with no clamped floor, one breathing band above the peak capped at rank 12, axis labels positioned as a pure percentage of band centres.
- Same-employer staircase grouped by company across the whole role list, drawn as one translucent layer.
- Lane-splitting for concurrent same-rank roles; touching at a month boundary is not overlap.
- Solid dominant-family bars, sphere palette by rank, estimated-date hatching, tooltip, legend filtering, bar-click scroll-to-role.
- Attribution banner, Save as PDF, and the print stylesheet.
- Boomerang re-engagement notes, auto-detected from dates and company names (`roles[].boomerang_note` overrides the wording).

Full field-by-field detail is in `reference/viewer-contract.md`. The rendering rules themselves, and why each exists, are in `docs/visualization-technical-spec.md`.

## Changing the viewer

A rendering rule changes in one place: `viewer/career-profile.html`. Per-candidate edits to a built HTML file are not allowed, because they reintroduce exactly the drift this design removed. If a page renders wrong, the fix is in the JSON or in the viewer.

After any change:

1. `python3 scripts/check_viewer.py` - fails if the viewer's copied levels or palette drift from `reference-data/` and the spec, if the spec version stamp disagrees, or if the profile-data slot or the print handler went missing.
2. Rebuild `reference-data/example-structured.json` and look at it. The fixture deliberately exercises a rank-0 P1 floor, two same-employer staircases, a never-dominant secondary family, a concurrent same-rank side gig, and an off-chart role.
3. Check the chart at roughly 900px and 480px wide. Axis-label drift as the window narrows is the signature failure of the overlay geometry.
4. Update `docs/visualization-technical-spec.md` (including its version and changelog), `reference/viewer-contract.md` if a field's meaning changed, and the version table in `SKILL.md`.

## Attribution (LOCKED)

The page carries a banner at the top reading "This resume visualization was created using an AI skill." with the copyright holder **Anton Nadey**, linked to `github.com/koryazh/resume-parsing-visualization`. It is in the viewer already; do not rewrite it, and never attribute this skill to Anthropic or link it to `github.com/anthropics/skills`. A user may switch the banner off for a profile with `render_options.show_attribution_banner: false`, and it must not be re-added once removed, but its wording and link are not edited.

## Contract dependency

This phase reads JSON schema v1.0 plus the additive fields listed in `reference/viewer-contract.md` (`role_synthesis`, `boomerang_note`, `render_options`, and the non-rendering capture fields). It fails loudly - a visible error screen listing the missing paths - rather than rendering something wrong.
