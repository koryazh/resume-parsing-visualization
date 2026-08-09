---
name: resume-parsing-visualization
description: Turn a resume PDF into a structured JSON career profile with leveling and job-family weights, then render it as an interactive HTML career-ladder chart. Use for either phase, or the full pipeline.
---

## Overview

A two-phase pipeline in one skill: **Phase 1 (parsing)** converts a candidate's resume PDF into a structured JSON file with full career metadata - leveling, professional-sphere weights, industry, render policy, and audit trail. **Phase 2 (visualization)** renders that JSON as a single self-contained HTML file - a sticky interactive career-ladder chart on top, the full textual resume below. The JSON schema (v1.0) is the contract between the two phases.

This SKILL.md is a router. It doesn't repeat either phase's detailed rules - those live in `reference/parsing.md` and `reference/visualization.md`, and each is long enough that you should only load the one(s) you actually need for the task at hand.

## Which phase to run

- **Given a resume PDF, no structured.json yet** → Phase 1 only. Read `reference/parsing.md` in full before starting.
- **Given a structured.json (or an existing career-ladder HTML to refresh)** → Phase 2 only. Read `reference/visualization.md` in full before starting. You do not need `reference/parsing.md` for this.
- **Given a resume PDF with the end goal of a rendered chart** → run Phase 1 first. Surface borderline leveling/family calls to the user per `reference/parsing.md`'s Step 3 and get sign-off on the JSON before moving to Phase 2 - don't skip straight to rendering from an unconfirmed parse.
- **Given a LinkedIn export alongside an existing structured.json** → a Phase 1 re-pass (augmentation). Read `reference/parsing.md`'s "LinkedIn augmentation" section.
- **Given a request to add a job family/industry, or to adjust a visual/leveling rule** → read the relevant reference file's own guidance before editing (`reference/parsing.md` owns leveling + taxonomy rules; `reference/visualization.md` owns rendering rules), then also update `reference-data/job-families-and-industries.json` or `reference-data/leveling-framework.json` as needed. Adding an `example_title` or a `title_trap` needs no version bump; changing a level's `rank` does and breaks every existing `structured.json`.

## Shared contract: JSON schema v1.0

Both phases are built around one JSON contract, defined in full in `reference/parsing.md`'s `Schema (v1.0)` section. Phase 1 produces it; Phase 2 consumes specific field paths from it (`roles[].strata`, `roles[].family_tags`, `aggregates.professional_spheres_ranked_by_dominant`, etc.) and fails loudly if a required field is missing. Keep changes to this schema backward-compatible where possible; bump `$schema_version` for breaking changes, and keep both reference files in sync with the bump.

## Reference data (used by Phase 1)

- `reference-data/leveling-framework.json` - the 13-level career strata framework (v3.0), 7 dimensions per level, plus `example_titles` and `title_traps` per level and file-level `leveling_notes`. Required reading before any parsing pass.
- `reference-data/job-families-and-industries.json` - the job-family/industry taxonomy, currently v2.0 (35 families, 27 industries). Required reading before any parsing pass.

## Companion docs (used by / about Phase 2)

- `docs/visualization-technical-spec.md` - the portable technical spec for the visualization phase; also useful outside this skill system. Current version 1.2 (2026-07-19): default bar encoding is solid dominant-family-color (striped remains a documented alternate), plus locked page-density/divider/hero-alignment defaults.
- `docs/how-visualization-works.md` - reader-facing narrative explaining the rendered chart to someone opening it for the first time (e.g. a hiring manager). Not required reading for Claude to do the rendering, but good to point a user at if they ask what the chart means.

## Versioning & contract stability

- JSON schema version: currently `1.0`. Additive fields are fine without a bump; breaking changes require a bump and synchronized updates to `reference/visualization.md`.
- Leveling framework version: currently `3.0` (2026-08-09). Converted from xlsx to JSON; P1 added at **rank 0** specifically so that ranks 1-12 (P2 through C-Level) stay stable and no existing `structured.json` or chart axis is renumbered. Treat the rank contract in the file's `rank_contract` field as frozen.
- Taxonomy version: currently `2.0` (2026-07-19). Bump only if a family is split, merged, or removed; new families/industries can be added without a bump. v2.0 was a full restructuring (34 families, anchored on O*NET-SOC's public major groups) that replaced v1.1's narrower 21-family list; see `reference-data/job-families-and-industries.json`'s `notes` field for the full migration detail.
- A future standalone skill (e.g. `resume-job-matching`) could consume the same JSON - keep the schema contract stable for that reason too, independent of anything in this skill.
