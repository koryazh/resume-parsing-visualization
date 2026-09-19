---
name: resume-parsing-visualization
description: Turn a resume PDF into a structured JSON career profile with leveling and job-family weights, then render it as an interactive HTML career-ladder page with the bundled viewer. Use for either phase, or the full pipeline.
---

## Version

**Skill version 2.0, updated 2026-09-19.**

This is the same number as the GitHub release tag (`v2.0`) and the visualization spec, which is the component that moves most often. It is deliberately not a fourth independent version to keep in sync. The components below move on their own schedules:

| Component | Version |
|---|---|
| JSON schema | 1.0 (plus additive optional fields) |
| Leveling framework | 3.0 (13 levels, ranks 0-12) |
| Job family taxonomy | 2.0 (35 families, 30 industries) |
| Visualization spec | 2.0 |
| Bundled viewer | 1.0.0 |

**Update the line above in the same commit that bumps any component.** A stale version stamp is worse than no version stamp, because it is the first thing a reader trusts and the last thing they re-check.

**What changed in 2.0:** Phase 2 no longer writes HTML. The skill ships a finished renderer, `viewer/career-profile.html`, that draws any conforming JSON in the browser, and `scripts/build_profile.py` bakes a JSON into it. Every chart is now produced by the same code instead of being re-implemented per candidate, which is what the 1.8 and 1.9 changelog entries were about. The model's remaining output per render is the two composed AI-synthesis texts, which Phase 1 writes into the JSON.

## Overview

A two-phase pipeline in one skill: **Phase 1 (parsing)** converts a candidate's resume PDF, or a LinkedIn profile export, into a structured JSON file with full career metadata - leveling, professional-sphere weights, industry, render policy, composed synthesis texts, and audit trail. **Phase 2 (visualization)** turns that JSON into a single self-contained HTML file by running a script over the bundled viewer: a sticky interactive career-ladder chart on top, the full textual resume below. The JSON schema (v1.0) is the contract between the two phases.

This SKILL.md is a router. It doesn't repeat either phase's detailed rules - those live in `reference/parsing.md` and `reference/visualization.md`, and each is long enough that you should only load the one(s) you actually need for the task at hand.

## The flow

```
resume PDF / LinkedIn export
   |
   |  Phase 1  (reference/parsing.md)
   v
structured.json  ── includes career_synthesis + role_synthesis for 8+ bullet roles
   |
   |  Step 3 gate: surface every borderline call and WAIT for the user
   v
python3 scripts/validate_structured_json.py <json>      errors must reach zero
   |
   |  Phase 2  (reference/visualization.md)
   v
python3 scripts/build_profile.py <json> -o <Name>_career-ladder.html
   |
   v
deliver BOTH files: the HTML and the JSON it was built from
```

## Which phase to run

- **Given a resume PDF or LinkedIn export, no structured.json yet** → Phase 1. Read `reference/parsing.md` in full before starting.
- **Given a structured.json (or an existing career-ladder HTML to refresh)** → Phase 2 only: validate, then build. Read `reference/visualization.md` first; it is short now. You do not need `reference/parsing.md`.
- **Given a PDF with the end goal of a rendered chart** → Phase 1, then the Step 3 gate, then Phase 2. Do not skip straight to rendering from an unconfirmed parse.
- **Given a LinkedIn export alongside an existing structured.json** → a Phase 1 re-pass (augmentation). Read `reference/parsing.md`'s "LinkedIn augmentation" section.
- **Given a request to add a job family/industry, or to adjust a visual/leveling rule** → read the relevant reference file's own guidance before editing (`reference/parsing.md` owns leveling + taxonomy rules; `reference/visualization.md` owns rendering rules), then update `reference-data/job-families-and-industries.json`, `reference-data/leveling-framework.json`, or `viewer/career-profile.html` as needed. Adding an `example_title` or a `title_trap` needs no version bump; changing a level's `rank` does and breaks every existing `structured.json`.

## Step 3 is a blocking gate

Between the two phases, surface every borderline call and wait for an answer: every role that will not appear on the chart, every "Manager"-titled role, side gigs that overlap the main career, roles whose bullets are too thin to level confidently, any call whose reversal would reorder the top two professional spheres, and any taxonomy gap. A default exists so there is somewhere to land once the user answers, not so the question can be skipped. `reference/parsing.md` carries the full list and the reasoning.

## Scripts

All standard library, no install step.

- `scripts/build_profile.py` - **Phase 2.** Bakes a `structured.json` into `viewer/career-profile.html` and writes the delivered page. Re-runs the validator first and refuses to build while any ERROR stands (`--skip-validate` overrides, only for a JSON the user has knowingly accepted). Prints the role and employer counts the page header will show, so they can be checked against the chart.
- `scripts/validate_structured_json.py` - validates a `structured.json` against schema v1.0 and cross-checks it against both reference-data files. **Run between the two phases**, and again after any hand-edit. Exit 0 = contract holds. `--strict` fails on warnings, `--json` gives machine-readable output.
- `scripts/test_validator.py` - self-test for the validator: breaks the bundled fixture many different ways and asserts each is caught, including the warning-only cases. Run it after changing the schema, the validator, or either reference-data file.
- `scripts/check_viewer.py` - self-test for the viewer: fails if its copied levels or palette drift from `reference-data/` and the spec, if the spec version stamp disagrees, or if the profile-data slot or the print handler went missing. Run it after touching the viewer, the framework, or the palette, and before packaging.

## The viewer

`viewer/career-profile.html` is the single implementation of the visualization spec. It is self-contained apart from Google Fonts, and it reads a profile from four places, in order: the JSON baked into it by the build script; `?data=<url>` when hosted; `?data=storage:<key>` from browser storage; or a file the reader drops onto its loader screen.

**Never hand-write a career-ladder page, and never hand-edit a built one.** If something renders wrong, the fix belongs in the JSON or in the viewer. Per-candidate HTML is what this version removed.

If the environment cannot run Python at all, deliver the JSON plus `viewer/career-profile.html` and tell the user to drop one onto the other. Same result, two files.

## Reference data (used by Phase 1)

- `reference-data/leveling-framework.json` - the 13-level career strata framework (v3.0), 7 dimensions per level, plus `example_titles` and `title_traps` per level and file-level `leveling_notes`. Required reading before any parsing pass.
- `reference-data/job-families-and-industries.json` - the job-family/industry taxonomy, currently v2.0 (35 families, 30 industries). Required reading before any parsing pass.
- `reference-data/example-structured.json` - a **synthetic** (fabricated, not a real candidate) reference document showing a complete valid parse. Deliberately exercises a rank-0 P1 role, two same-employer staircases, a never-dominant secondary family, a concurrent same-rank side gig, and an off-chart pre-career role. Doubles as the fixture for `scripts/test_validator.py`.

## Companion docs

- `reference/viewer-contract.md` - every JSON path the viewer reads, everything it computes for itself, and the additive fields (`role_synthesis`, `boomerang_note`, `render_options`, capture-only fields). Read it when a page is missing something you expected.
- `docs/visualization-technical-spec.md` - the portable technical spec for the visualization phase, also useful outside this skill system. Current version 2.0.
- `docs/how-visualization-works.md` - reader-facing narrative explaining the rendered chart to someone opening it for the first time (e.g. a hiring manager). Good to point a user at if they ask what the chart means.

## Attribution (LOCKED)

The rendered page carries an attribution banner whose text and link are fixed: **the copyright holder is Anton Nadey** and the repository is **`github.com/koryazh/resume-parsing-visualization`**. Never attribute this skill to Anthropic and never link it to `github.com/anthropics/skills`. This is not an Anthropic product. The banner is already in the viewer; do not rewrite it. A user may switch it off for a profile with `render_options.show_attribution_banner: false`, and it must not be re-added once removed.

## Versioning & contract stability

- JSON schema version: currently `1.0`. Additive optional fields (`role_synthesis`, `boomerang_note`, `render_options`, `candidate.headline`, `candidate.top_skills`) are fine without a bump, and a consumer that does not know them ignores them. Breaking changes require a bump and synchronized updates to `reference/visualization.md` and `reference/viewer-contract.md`.
- Leveling framework version: currently `3.0` (2026-08-09). P1 sits at **rank 0** specifically so that ranks 1-12 (P2 through C-Level) stay stable and no existing `structured.json` or chart axis is renumbered. Treat the rank contract in the file's `rank_contract` field as frozen. The viewer carries a copy of the levels; `scripts/check_viewer.py` guards it.
- Taxonomy version: currently `2.0` (2026-07-19). Bump only if a family is split, merged, or removed; new families/industries can be added without a bump. See `reference/parsing.md` on where such an addition may be made - inside the source repository it is a file edit, from an installed copy it is a proposal recorded in `data_quality`.
- A future standalone skill (e.g. `resume-job-matching`) could consume the same JSON - keep the schema contract stable for that reason too, independent of anything in this skill.
