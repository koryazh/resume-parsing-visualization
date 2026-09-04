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

| Phase | Input | Output |
|---|---|---|
| 1. Parsing | Resume PDF | `<Candidate>_structured.json` (schema v1.0) |
| 2. Visualization | The structured JSON | `<Candidate>_career-ladder.html` |

The JSON schema is the contract between the phases. Phase 1 assigns every role a career level (strata), weighted job-family tags, an industry, and a render policy, with an audit trail for borderline calls. Phase 2 consumes that JSON and renders a sticky interactive chart (time on the x-axis, career level on the y-axis, bar color by dominant professional sphere) above the full textual resume.

Either phase can run on its own. Phase 2 never needs the parsing rules, and vice versa.

## Layout

```
SKILL.md                                    router: which phase to run, versions, contract stability
reference/parsing.md                        Phase 1 rules: leveling, taxonomy, schema, edge cases
reference/visualization.md                  Phase 2 rules: geometry, encoding, palette, locked rules
reference-data/leveling-framework.json      13-level career strata framework (v3.0)
reference-data/job-families-and-industries.json   job family and industry taxonomy (v2.0)
reference-data/example-structured.json      synthetic reference document, also the validator fixture
scripts/validate_structured_json.py         checks a structured JSON against the schema and reference data
scripts/test_validator.py                   self-test for the validator, 16 cases
docs/visualization-technical-spec.md        portable rendering spec, usable outside this skill
docs/how-visualization-works.md             reader-facing explainer for someone opening the chart
```

`SKILL.md` is a router, not a manual. It deliberately does not repeat the phase rules, so load only the reference file for the phase you are running.

## Versions

| Component | Version | Notes |
|---|---|---|
| JSON schema | 1.0 | Contract between the two phases. Additive fields are fine; breaking changes need a bump. |
| Leveling framework | 3.0 | 13 levels, 7 dimensions each, plus `example_titles` and `title_traps` per level. |
| Job family taxonomy | 2.0 | 35 families anchored on O*NET-SOC major groups, 28 industries. |
| Visualization spec | 1.9 | Solid dominant-family-color bars by default. Rank range 0-12; axis-overlay alignment rules locked; C-Level peak-label collapse and boomerang-re-engagement company notes; full-career synthesis block, timed attribution banner, and Save as PDF with a print stylesheet. Attribution wording, the print stylesheet, and the Save as PDF control are locked copy-paste blocks; tenure-header counts are on-chart only. |

Rank contract: P1 sits at rank 0, added in v3.0. Ranks 1 through 12 are stable and must never be renumbered, because every previously generated `structured.json` encodes them.

## Editing rules worth knowing

These are the ones that bite hardest if missed. Full detail lives in the reference files.

- Roles are stored forward-chronologically in the JSON (`role_1` is the earliest), and rendered reverse-chronologically in the HTML. Getting this backwards silently inverts the whole Experience section.
- Resume bullets are captured and rendered verbatim. Never paraphrase, reword, combine, or truncate.
- Education dates are never captured and never rendered, to protect candidates from age-based screening.
- No em dash in any text the model itself writes. Verbatim candidate content is exempt and stays exactly as the resume had it.
- Adding a family or industry to the taxonomy does not require a version bump. Splitting, merging, or removing one does.
- Changing a level's `rank` is a breaking change and invalidates every existing structured JSON.

## Candidate data

No real candidate files belong in this repository. The skill is portable by design and ships with no resumes and no rendered charts. Generated output stays wherever it was produced. `.gitignore` blocks the common cases as a backstop.

The one bundled JSON, `reference-data/example-structured.json`, is a fabricated fixture with an invented candidate. It exists so the schema has a concrete reference and so the validator has something to self-test against.

## Validating a structured JSON

```bash
python3 scripts/validate_structured_json.py path/to/structured.json
```

Run it between the two phases and after any hand-edit of the JSON. Exit 0 means the contract holds; exit 1 means Phase 2 would render incorrectly. `--strict` fails on warnings, `--json` gives machine-readable output. Standard library only, no install step.

After changing the schema, the validator, or either reference-data file, run `python3 scripts/test_validator.py`. It breaks the bundled fixture 16 different ways and asserts each one is caught, which is what tells you the fixture has gone stale.

## License

Copyright (c) 2026 Anton Nadey. All rights reserved. See [LICENSE](LICENSE).

You may download and use this skill, unmodified, to process your own resume data for personal or internal business purposes. Redistribution, derivative works, and offering it as a service require written permission. No patent rights are granted.

If you want to use this beyond those terms, get in touch.

## For maintainers

This repository is the source of truth for the skill. Edit here, commit, then package:

```bash
./package.sh
```

That writes two files into `dist/`: a timestamped build record, `resume-parsing-visualization-skill-YYYY-MM-DD-HHMM.zip`, and a constant-named copy, `resume-parsing-visualization-skill.zip`, which is the one to attach to a GitHub release. The asset name must stay constant or the permanent `releases/latest/download/` link above breaks. macOS cruft is excluded from both.

Publishing a new version means cutting a release with that asset attached, not committing a zip to the repository. The full release protocol lives in the separate `resume-par-vis-skill-release` skill.
