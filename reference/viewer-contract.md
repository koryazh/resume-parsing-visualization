# Viewer contract: what `viewer/career-profile.html` reads

Companion to `reference/visualization.md`. It lists every JSON path the bundled viewer touches, everything it works out for itself, and the additive fields Phase 1 may write. Keep it current in the same edit that changes the viewer.

## Where the viewer gets the JSON

In order of precedence:

1. **The embedded `profile-data` block**, written by `scripts/build_profile.py`. This is the delivered artefact: one self-contained file.
2. **`?data=<url>`**, fetched when the viewer is hosted (`career-profile.html?data=profiles/jane.json`). Cross-origin JSON needs CORS headers, and this does not work from `file://`.
3. **`?data=storage:<key>`**, a profile held in the browser's `localStorage`, either the profile JSON itself or `{ name, text }` wrapping its raw text. Used by local tooling that lets someone pick a file.
4. **The loader screen**, shown when there is no data: a file picker plus drag-and-drop, so a user handed the bare viewer and a JSON can open it without any tooling. Nothing is uploaded; the file is read in the browser.

The viewer consumes the `structured.json` produced by Phase 1 (schema v1.0, defined in `reference/parsing.md`). It does not define a new schema.

## Required (the page shows an error screen without them)

| Field | Rule |
|---|---|
| `candidate.name` | non-empty string |
| `roles` | non-empty array |
| `roles[].id`, `.company`, `.title` | non-empty strings; `id` unique |
| `roles[].start_date` | `"YYYY-MM"` |
| `roles[].end_date` | `"YYYY-MM"` or `"current"`, not before `start_date` |
| `roles[].strata.rank` | integer 0-12, for every on-chart role |
| `roles[].family_tags[]` | non-empty, each with `family_id` and numeric `weight`, for every on-chart role |
| at least one on-chart role | otherwise there is nothing to draw |

`$schema_version`, when present, must be `1.x`. `scripts/build_profile.py` runs these same checks, after the full validator, before it builds.

These are the viewer's minimum, not the full contract. Arithmetic and cross-reference errors (weights not summing to 1.0, a `code` that disagrees with its `rank`, a family id missing from the taxonomy) still render, just wrongly. `scripts/validate_structured_json.py` catches those, and `scripts/build_profile.py` refuses to build while any of them stand.

## Read when present

| Field | Used for |
|---|---|
| `generated` | the "as of" month that `"current"` roles run to (same convention as the validator) |
| `candidate.contact.phone`, `.email`, `.linkedin` | hero contacts row (nothing else from `contact` except the next line) |
| `candidate.contact.location`, `.work_authorization` | hero location line |
| `candidate.career_synthesis` | collapsed full-career AI synthesis panel (composed in Phase 1) |
| `candidate.education[]` (`institution`, `degree`, `field`) | Education, never with dates |
| `candidate.certifications[]` (`name`, or plain strings) | inline list under Education |
| `candidate.honors[]` | Honors section |
| `candidate.tech_stack` (`domain_specific`, `general_purpose`, other keys) | Tech Stack section, if tech-adjacent (below) |
| `roles[].render_policy.on_chart`, `.in_experience_text` | chart vs. text inclusion (both default to true) |
| `roles[].is_estimated` | hatched, faded bar; year-only dates |
| `roles[].single_sentence` | tooltip label; never striped |
| `roles[].narrative_bullets[]` | verbatim bullets |
| `roles[].company_history_note` | italic note on the most recent role at that employer |
| `roles[].title_history_note` | italic note on that role |
| `roles[].industry.id` | tech-adjacent test only |
| `roles[].family_tags[].family_name` | legend and tooltip names (falls back to a humanized id) |
| `internships[]` | compact block at the end of Experience, never on the chart |
| `aggregates.professional_spheres_ranked_by_dominant[].family_id` | tie-break order only |

## Derived by the viewer, never read

Everything the chart header and legend print is computed from the on-chart roles, so the numbers always describe the bars on screen:

- **Career path span** - first on-chart start month to last on-chart end month, inclusive.
- **N roles / M employers** - on-chart roles and distinct on-chart `company` values.
- **Peak job level** - the highest on-chart `strata.rank`; code and name come from the leveling framework, printed once when they are identical (`C-Level`).
- **Strata bands** - lowest on-chart rank up to one band above the peak, capped at 12. Labels come from the framework, not from `strata.code`.
- **Sphere ranking and legend months** - months-where-dominant per family over on-chart roles. Ties follow the stored `aggregates` order, then `family_id` A-Z.
- **Colours** - by sphere rank (spec 5.8); families that are never dominant take the next ranks and get no legend pill.
- **Boomerang notes** (spec 4.6) - a role gets "Second engagement - previously <title>, <dates>" when an earlier stint at the same `company` ended and a different employer's role began before this one started.

`aggregates.career_length_label`, `role_count`, `employer_count`, `peak_strata`, and sphere `months`/`color` are ignored on purpose. A stored aggregate computed over a different role set is exactly the bug spec v1.9 recorded (a header reading "9 roles" above 8 bars). Note the resulting split of responsibility: `aggregates.employer_count` in the JSON counts distinct companies across **all** roles (what the validator checks), while the header counts the **on-chart** employers the reader can see. Both are right; they answer different questions.

## Additive fields this viewer understands (schema v1.0 compatible)

All optional. Consumers that do not know them ignore them.

### `roles[].role_synthesis` (string)

The composed 2-3 sentence TL;DR for a role with **8 or more bullets**, shown in the per-role `AI SYNTHESIS` panel. Before spec 2.0 the model composed this while writing the HTML by hand; the viewer cannot compose, so Phase 1 writes it into the JSON. The validator warns when a role has 8+ bullets and no `role_synthesis`. Ignored on roles with fewer than 8 bullets. Same rules as `career_synthesis`: every claim checkable against the bullets, no praise, no invented metrics.

`narrative_summary` is **not** used for this panel, because its provenance (verbatim vs. composed) is not fixed by the schema, and the panel label asserts the text is composed.

### `roles[].boomerang_note` (string)

Overrides the auto-detected boomerang note for that role. Use it when detection gets the wording wrong, for example when the earlier stint should be described differently.

### `render_options` (object, top level)

| Key | Values | Default |
|---|---|---|
| `bar_style` | `"solid"` or `"striped"` (weight-proportional stripes, the documented alternate) | `"solid"` |
| `as_of` | `"today"` (browser date) or `"YYYY-MM"` | the `generated` month |
| `show_tech_stack` | `true` / `false` | auto: shown when any on-chart role has a tech family (`engineering_software`, `data_science_ai_ml`, `product_management`, `engineering_technical`, `it_infrastructure_systems_administration`) or a tech industry |
| `tech_stack_labels` | `{ "domain_specific": "HR / TA platforms", ... }` | "Domain specific", "General purpose" |
| `extra_sections` | array of `candidate` keys, e.g. `["languages"]` | none (section conservatism) |
| `show_attribution_banner` | `false` removes the banner | shown |

`extra_sections` is how an explicit user request for a normally suppressed section (Languages, Top Skills, Interests, and the rest of spec 4.5's list) is recorded. Only add a key when the user asked for that section on that profile.

## Capture-only fields

Phase 1 also writes fields the viewer deliberately never renders, so that downstream consumers (job matching, search) have them: `candidate.summary`, `candidate.headline`, `candidate.top_skills`, `candidate.languages`, `candidate.areas_of_expertise`, every `reasoning` string, and `data_quality`. Section conservatism governs which of them a user can opt into with `render_options.extra_sections`; `summary` and `headline` are never rendered at all, because the hero rule is strict.

## Where the viewer gets its framework constants

The 13 levels and the sphere palette are copied into the viewer between `LEVELS:BEGIN/END` and `PALETTE:BEGIN/END` markers, because the page must draw without reading this skill's files. `scripts/check_viewer.py` fails if those copies drift from `reference-data/leveling-framework.json` or the palette table in `docs/visualization-technical-spec.md`.
