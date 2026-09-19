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
| 2. Visualization | The structured JSON | `<Candidate>_career-ladder.html` | `python3 scripts/build_profile.py <json>` bakes it into the bundled viewer |

The JSON schema is the contract between the phases. Phase 1 assigns every role a career level (strata), weighted job-family tags, an industry, and a render policy, with an audit trail for borderline calls. Phase 2 consumes that JSON and renders a sticky interactive chart (time on the x-axis, career level on the y-axis, bar color by dominant professional sphere) above the full textual resume.

**Since v2.0 the page is drawn by one bundled renderer, `viewer/career-profile.html`, not written per candidate.** Same design, same rules, produced by the same code every time. The viewer also works on its own: open it and drop a structured JSON onto it, or host it and call `career-profile.html?data=<url-to-json>`.

Either phase can run on its own. Phase 2 never needs the parsing rules, and vice versa.

## How a render runs

```
resume PDF or LinkedIn export
  |  Phase 1: parse, level, tag, and compose the two AI-synthesis texts
  v
<Candidate>_structured.json
  |  borderline calls surfaced to the user, then:
  |  python3 scripts/validate_structured_json.py <json>
  |  python3 scripts/build_profile.py <json>
  v
<Candidate>_career-ladder.html   + the JSON it was built from
```

`build_profile.py` re-runs the validator and refuses to write the page while any error stands, then prints the role and employer counts the page header will show, so they can be checked against the chart. Both scripts are standard-library Python 3 with no install step.

## New in v2.0

- **The page is rendered, not written.** `viewer/career-profile.html` implements the whole visualization spec once and reads any conforming JSON. Earlier versions had the model write a fresh page per candidate, which is where the drift recorded in the v1.8 and v1.9 spec changelogs came from. Renders are now faster, cheaper, and identical in structure.
- **The header cannot contradict the chart.** Career span, role and employer counts, peak level, sphere ranking and legend durations are computed from the on-chart roles at render time rather than read from stored aggregates.
- **Composed prose lives in the JSON.** `candidate.career_synthesis` and the new `roles[].role_synthesis` (for roles with 8+ bullets) are written during parsing; the renderer displays them and never invents text. The validator warns when either is missing.
- **`render_options`** carries per-profile choices a user asks for: bar style, as-of month, tech-stack visibility, opt-in sections, and whether the attribution banner shows.
- **LinkedIn profile exports** are documented as a first-class source: prose paragraphs as bullets, title-only roles (now a warning, not an error), shared boundary months, and internal moves that look like a company change.
- **`scripts/check_viewer.py`** guards the constants the viewer has to carry (levels, palette, spec stamp) against the reference data they were copied from.

## Layout

```
SKILL.md                                    router: which phase to run, versions, contract stability
reference/parsing.md                        Phase 1 rules: leveling, taxonomy, schema, edge cases
reference/visualization.md                  Phase 2 rules: validate, build, verify, deliver
reference-data/leveling-framework.json      13-level career strata framework (v3.0)
reference-data/job-families-and-industries.json   job family and industry taxonomy (v2.0)
reference-data/example-structured.json      synthetic reference document, also the validator fixture
viewer/career-profile.html                  the renderer: draws any conforming JSON in the browser
scripts/build_profile.py                    Phase 2: validates, then bakes a JSON into the viewer
scripts/validate_structured_json.py         checks a structured JSON against the schema and reference data
scripts/test_validator.py                   self-test for the validator
scripts/check_viewer.py                     self-test for the viewer (levels, palette, spec stamp, slots)
reference/viewer-contract.md                every JSON path the viewer reads, computes, or ignores
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
| Visualization spec | 2.0 | Rendering moved from per-candidate HTML to the bundled viewer. Header, legend and sphere ranking computed from the on-chart roles; composed synthesis texts read from the JSON; single translucent same-employer staircase; `render_options` for per-profile choices. Earlier rules (solid dominant-family bars, rank range 0-12, axis-overlay alignment, C-Level label collapse, boomerang notes, attribution banner, Save as PDF and the print stylesheet) are unchanged and now enforced in code. |
| Bundled viewer | 1.0.0 | `viewer/career-profile.html`. Reads a baked-in profile, `?data=<url>`, browser storage, or a dropped file. |

Rank contract: P1 sits at rank 0, added in v3.0. Ranks 1 through 12 are stable and must never be renumbered, because every previously generated `structured.json` encodes them.

## Editing rules worth knowing

These are the ones that bite hardest if missed. Full detail lives in the reference files.

- Role ids carry no ordering meaning to the renderer: the viewer sorts by date (chart ascending, Experience reverse-chronological). Keep whatever order the parse produced; the bundled fixture numbers from the most recent role.
- Resume bullets are captured and rendered verbatim. Never paraphrase, reword, combine, or truncate.
- Education dates are never captured and never rendered, to protect candidates from age-based screening.
- No em dash in any text the model itself writes. Verbatim candidate content is exempt and stays exactly as the resume had it.
- Adding a family or industry to the taxonomy does not require a version bump. Splitting, merging, or removing one does. An installed copy of the skill is per-session, so such an addition has to be made in this repository, not in the copy a parse is running from.
- Never hand-write a career-ladder page or hand-edit a built one. A rendering fix belongs in `viewer/career-profile.html`, a content fix in the JSON.
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
