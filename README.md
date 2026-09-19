# resume-parsing-visualization

A Claude skill that turns a resume PDF into a structured JSON career profile, then renders that profile as an interactive HTML career-ladder chart.

## Install

Download the packaged skill from the latest release:

**[Download the latest version](https://github.com/koryazh/resume-parsing-visualization/releases/latest/download/resume-parsing-visualization-skill.zip)**

That link always resolves to the most recent release, so it is safe to bookmark or share.

Then add it to Claude:

1. Open Claude's settings and go to Capabilities, then Skills.
2. Choose to upload a skill and select the downloaded `.zip`.
3. The skill appears as `resume-parsing-visualization` and is available in new conversations.

Ask Claude to parse a resume PDF, or to render a chart from a structured JSON you already have, and it will pick up the skill automatically.

**Do not use the green "Code" button's "Download ZIP".** That produces a source archive with the branch name appended to the folder and repository scaffolding included, which is not a valid skill package. Use the release link above.

## What it does

Two phases, one contract:

| Phase | Input | Output | How |
|---|---|---|---|
| 1. Parsing | Resume PDF or LinkedIn export | `<Candidate>_structured.json` (schema v1.0) | Claude reads the source against the leveling framework and taxonomy |
| 2. Visualization | The structured JSON | `<Candidate>_career-ladder.html` | The skill builds the page from the profile |

The JSON schema is the contract between the phases. Phase 1 assigns every role a career level (strata), weighted job-family tags, an industry, and a render policy, with an audit trail for borderline calls. Phase 2 consumes that JSON and renders a sticky interactive chart (time on the x-axis, career level on the y-axis, bar color by dominant professional sphere) above the full textual resume.

Either phase can run on its own. Phase 2 never needs the parsing rules, and vice versa.

## How a render runs

```
resume PDF or LinkedIn export
  |  Phase 1: parse, level, tag, and compose the career summaries
  v
<Candidate>_structured.json
  |  borderline calls surfaced to you and answered, then checked against the contract
  v
<Candidate>_career-ladder.html   + the JSON it was built from
```

You get both files. The JSON is what a later re-render, an edit, or any other use of the profile needs.

## New in v2.0

- **Pages are built, not written from scratch.** Earlier versions composed a fresh page for each candidate, which made renders slow and let details drift between them. Renders are now faster and every page comes out with the same structure.
- **The header cannot contradict the chart.** Career span, role and employer counts, peak level, sphere ranking and legend durations are computed from the on-chart roles at render time rather than read from stored aggregates.
- **Written summaries live in the profile.** The full-career summary and the new per-role summary (for roles with 8 or more bullets) are produced during parsing and stored in the JSON, so the page never invents text.
- **`render_options`** carries per-profile choices a user asks for: bar style, as-of month, tech-stack visibility, opt-in sections, and whether the attribution banner shows.
- **LinkedIn profile exports** are documented as a first-class source: prose paragraphs as bullets, title-only roles (now a warning, not an error), shared boundary months, and internal moves that look like a company change.

## Layout

```
SKILL.md                                    router: which phase to run, versions, contract stability
reference/parsing.md                        Phase 1 rules: leveling, taxonomy, schema, edge cases
reference/visualization.md                  Phase 2 rules: validate, build, verify, deliver
reference-data/leveling-framework.json      13-level career strata framework (v3.0)
reference-data/job-families-and-industries.json   job family and industry taxonomy (v2.0)
reference-data/example-structured.json      synthetic reference document, also the validator fixture
scripts/validate_structured_json.py         checks a structured JSON against the schema and reference data
scripts/test_validator.py                   self-test for the validator
docs/visualization-technical-spec.md        portable rendering spec, usable outside this skill
docs/how-visualization-works.md             reader-facing explainer for someone opening the chart
```

`SKILL.md` is a router, not a manual. It deliberately does not repeat the phase rules, so load only the reference file for the phase you are running.

## Versions

| Component | Version | Notes |
|---|---|---|
| JSON schema | 1.0 | Contract between the two phases. Additive fields are fine; breaking changes need a bump. |
| Leveling framework | 3.0 | 13 levels, 7 dimensions each, plus `example_titles` and `title_traps` per level. |
| Job family taxonomy | 2.0 | 35 families anchored on O*NET-SOC major groups, 30 industries. |
| Visualization spec | 2.0 | Pages are built rather than composed per candidate. Header, legend and sphere ranking computed from the roles on the chart; written summaries carried in the JSON; `render_options` for per-profile choices. Earlier rules (solid dominant-family bars, rank range 0-12, axis-overlay alignment, C-Level label collapse, boomerang notes, attribution banner, Save as PDF and the print stylesheet) are unchanged. |

Rank contract: P1 sits at rank 0, added in v3.0. Ranks 1 through 12 are stable and must never be renumbered, because every previously generated `structured.json` encodes them.

### Version history

Newest first. Releases are published from v1.6 onward; earlier versions predate the public packaging.

| Version | Date | What changed |
|---|---|---|
| 2.0 | 2026-09-19 | Pages are built rather than composed per candidate, so renders are faster and consistent. Header and legend computed from the roles on the chart; written summaries carried in the JSON; `render_options` for per-profile choices; LinkedIn exports supported as a source; staircase seam fix. |
| 1.9 | 2026-09-04 | Save as PDF control restored, tenure-header counts limited to on-chart roles, Phase 1 borderline calls made a blocking gate. |
| 1.8 | 2026-09-04 | Attribution wording and repository link locked; canonical print stylesheet block added. |
| 1.7 | 2026-09-04 | Full-career synthesis block, timed attribution banner, and Save as PDF with a print stylesheet. |
| 1.6 | 2026-08-23 | C-Level peak-label collapse; boomerang re-engagement notes under the company name. |
| 1.5 | 2026-08-23 | `C-Level` shortened to `C` in the strata axis overlay, display only. |
| 1.4 | 2026-08-09 | Strata axis-overlay alignment rules locked after a chart shipped with drifting labels. |
| 1.3 | 2026-08-09 | Aligned with leveling framework 3.0: rank range 0-12, floor never clamped. |
| 1.2 | 2026-07-19 | Solid dominant-family bars became the default; page density and divider rules. |
| 1.1 | 2026-07-18 | End dates given their own month convention, closing the same-employer staircase gap. |
| 1.0 | - | Original spec. |

## Editing rules worth knowing

These are the ones that bite hardest if missed. Full detail lives in the reference files.

- Role ids carry no ordering meaning: roles are placed by their dates (chart ascending, Experience reverse-chronological). Keep whatever order the parse produced; the bundled fixture numbers from the most recent role.
- Resume bullets are captured and rendered verbatim. Never paraphrase, reword, combine, or truncate.
- Education dates are never captured and never rendered, to protect candidates from age-based screening.
- No em dash in any text the model itself writes. Verbatim candidate content is exempt and stays exactly as the resume had it.
- Adding a family or industry to the taxonomy does not require a version bump. Splitting, merging, or removing one does. An installed copy of the skill is per-session, so such an addition has to be made in this repository, not in the copy a parse is running from.
- Never hand-edit a rendered page. A rendering fix belongs in the skill, a content fix in the JSON.
- Changing a level's `rank` is a breaking change and invalidates every existing structured JSON.

## Candidate data

No real candidate files belong in this repository. The skill is portable by design and ships with no resumes and no rendered charts. Generated output stays wherever it was produced. `.gitignore` blocks the common cases as a backstop.

The one bundled JSON, `reference-data/example-structured.json`, is a fabricated fixture with an invented candidate. It exists so the schema has a concrete reference and so the validator has something to self-test against.

## Validating a structured JSON

```bash
python3 scripts/validate_structured_json.py path/to/structured.json
```

Run it between the two phases and after any hand-edit of the JSON. Exit 0 means the contract holds; exit 1 means Phase 2 would render incorrectly. `--strict` fails on warnings, `--json` gives machine-readable output. Standard library only, no install step.

After changing the schema, the validator, or either reference-data file, run `python3 scripts/test_validator.py`. It breaks the bundled fixture many different ways and asserts each one is caught, including the warning-only cases, which is what tells you the fixture has gone stale.

## License

Copyright (c) 2026 Anton Nadey. All rights reserved. Patent pending. See [LICENSE](LICENSE).

You may download and use this skill, unmodified, to process your own resume data for personal or internal business purposes. Redistribution, derivative works, and offering it as a service require written permission. No patent rights are granted.

If you want to use this beyond those terms, get in touch.

## For maintainers

This repository is the source of truth for the skill. Edit here, commit, then package:

```bash
./package.sh
```

That writes two files into `dist/`: a timestamped build record, `resume-parsing-visualization-skill-YYYY-MM-DD-HHMM.zip`, and a constant-named copy, `resume-parsing-visualization-skill.zip`, which is the one to attach to a GitHub release. The asset name must stay constant or the permanent `releases/latest/download/` link above breaks. macOS cruft is excluded from both.

Publishing a new version means cutting a release with that asset attached, not committing a zip to the repository. The full release protocol lives in the separate `resume-par-vis-skill-release` skill.
