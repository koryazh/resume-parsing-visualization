## Phase 1 of 2: parsing

This is the parsing phase of the unified `resume-parsing-visualization` skill. It produces `structured.json`, which Phase 2 (`reference/visualization.md`) consumes to produce `career-ladder.html`. Read this file in full before starting a parse; you don't need `reference/visualization.md` unless you're also rendering the output in the same session.

The JSON schema is the contract between the two phases. Parsing changes shouldn't break the visualization phase as long as the schema stays backward-compatible. Bump `$schema_version` for breaking changes. (A future standalone skill, e.g. `resume-job-matching`, could also consume this same JSON - keep the contract stable for that reason too.)

## Required reading before parsing

Before starting a new parse, read:

- `reference-data/leveling-framework.json` - the 13-level career strata framework (v3.0), 7 dimensions per level. Anchors all strata assignments. Read `leveling_notes` and each level's `title_traps` and `example_titles` before leveling - the traps encode the title/scope mismatches that cause most mis-levels. Replaces the former `leveling-framework.xlsx`.
- `reference-data/job-families-and-industries.json` - the taxonomy of professional families (functional areas) and industries (vertical markets). Current version: **v2.0** (2026-07-19) - 35 families and 27 industries, anchored on O*NET-SOC's public major groups, replacing the narrower 21-family v1.1 list. The v2.0 restructuring itself produced 34 families; entries added additively since then carry no version bump and are logged in the file's `notes`. human_resources and talent_acquisition remain distinct sibling families as they were in v1.1 (id `human_resources` for HR & People Operations, id `talent_acquisition` for Talent Acquisition & Recruitment), unaffected by the v2.0 restructuring.

## The two-step workflow

**Step 1**: Extract the raw content from the resume PDF. Capture every role, every bullet, every date, verbatim. Do not paraphrase, summarize, or "improve" bullet wording - the visualization skill will render these verbatim downstream.

**Step 2**: For each role, assign:
- Strata (level) - read the bullets against the framework's 7 dimensions
- Family tags with weights summing to 1.0 across all families for that role
- Industry (single-valued)
- Role type (IC vs People Manager - reflects team-leadership, not level)
- Render policy (on-chart / in-experience-text)
- Data quality notes for any borderline call

**Step 3** (interactive): Surface borderline calls to the user via multiple-choice questions before finalizing the JSON. Common borderline calls:
- Any "Manager"-titled role (apply the decision tree below)
- Side gigs that overlap with main career
- Pre-career roles in a different family (on-chart vs off-chart decision)
- Ambiguous scope where bullets are minimal (1-2 lines only)

## Leveling framework - STRICT

Every role gets exactly one strata code from the framework. Never invent levels; only use the 13 defined below.

### Title-anchor heuristic (start here)

Start with the role's title; **adjust only with proof from the bullets**:

| Title contains | Default level |
|---|---|
| "Director" | **M5** Director |
| "Manager" | **M4** Manager |
| "Team Lead" / "Squad Lead" / "Supervisor" | **M3** Team Lead |
| "Tech Lead" | **P5** Lead - technical direction, no delegated people authority |
| Intern / Trainee / Apprentice / Co-op / "Entry-Level" / `I` suffix | **P1** Entry Professional (title-gated) |
| "VP" / "Vice President" | **E7** VP |
| "SVP" / "Senior Vice President" | **E8** SVP |
| "Chief X Officer" (CTO, CFO, COO, CEO, CPO, etc.) | **C-Level** |
| No manager title (Engineer, Generalist, HRBP, Analyst, Architect, Founder, etc.) | **P-track** by scope |

### Decision tree for "Manager"-titled roles (LOCKED)

The word "Manager" in a title is the most over-trusted signal in resumes - many "Manager"-titled roles are actually IC scope. **Do NOT auto-assign M4 just because the title says "Manager."** Read the bullets and decide:

1. **Bullets describe MANAGERIAL duties** (plans work + performance evaluations + salary decisions + budget participation + hire/fire authority over direct reports) → **M4 Manager**
2. **Bullets describe SUPERVISORY duties** (training and supervision of staff, task assignment, perf feedback, mentoring) but **final calls on hiring/salary/comp rest elsewhere** → **M3 Team Lead**
3. **Bullets describe NEITHER** managerial nor supervisory duties - sole-IC scope despite the title → **P4 Senior**

The distinction between (1) and (2) is *authority*, not *activity*. Both managers and team leads supervise people. M4 has final decision authority on hire/fire/comp/budget; M3 has delegated authority on those decisions but the final call rests with the manager-once-removed. If the bullets don't clarify which it is, ask the user before locking the call.

The same principle generalizes to other manager-flavored titles:
- **"Director"** (default M5) → if no managerial OR supervisory duties described, drop to P5 Lead (or P4 Senior if scope is narrow).
- **"VP" / "SVP" / "Chief X Officer"** → these typically carry executive scope; absence of managerial duties is rare and should be a strong red flag, surface to the user.

### Other adjustments

**Adjust UP** if a non-management title's bullets prove ownership at a higher level than the title suggests (rare but possible).

**Founder / Co-founder** is ambiguous - judge by bullets:
- Solo operator (built/developed/ran end-to-end, no team described) → P-track
- Founded with a small team they directly managed → M4
- Founded a substantial org with managers reporting up → M5+
- Real Executive Officer of an existing/scaled company → C-Level

### Level definitions

Each level definition has a **framework anchor** - the framework's dimension language that characterizes the level. Use these as reference points when leveling new roles.

**P-track (Individual Contributor):**
- **P1 Entry Professional** (rank 0) - **title-gated, unlike every other level**: assign only when the title itself carries an intern / trainee / apprentice / co-op / "Entry-Level" / `I`-suffix marker. Never infer P1 from thin bullets or short tenure; an unmarked title with P1-shaped scope is P2.
- **P2 Junior** (rank 1) - the widest band in the framework, since the P1 title-gate pushes every unmarked entry-scope role down here. Runs from supervised routine work (clerk, assistant, coordinator) at the bottom to near-independent "Junior X" delivery at the top.
- **P3 Middle** (rank 2) - fully productive IC, completes high-complexity tasks unsupervised, source of knowledge for juniors. Fits early-career roles where bullets describe full productivity within scope.
- **P4 Senior** (rank 3) - senior, often long-tenured IC, delivers technical/functional leadership and direction **within ONE domain**. Sole-owner scope of a domain (e.g. sole HR Generalist owning end-to-end HR at a small company) fits here.
- **P5 Lead** (rank 4) - IC, leads critical functional **initiatives or large programs**, develops new approaches to ambiguous problems. Look for explicit "Led ..." verbs in bullets; program-ownership language; novel initiative design. **"Tech Lead" belongs here, not M3** - technical direction without delegated authority over hiring, pay, or performance.
- **P6 Principal** (rank 5) - long-tenured IC, **company-wide** authority across 1+ domains, shapes company-wide strategy. Requires *company-wide* functional authority, not just senior partnership with one BU.

**M-track (People Manager):**
- **M3 Team Lead** (rank 6) - SOME managerial authority delegated (hiring manager input, task assignment, perf feedback) - final calls rest with manager-once-removed.
- **M4 Manager** (rank 7) - manages ICs directly = plans work + performance evaluation + salary decisions + budget participation.
- **M5 Director** (rank 8) - manages M3 Team Leads, owns department budget, participates in dept strategic planning.
- **M6 Senior Director** (rank 9) - manages M4 Managers, owns strategy + budget across a group of departments or one business unit.

**E-track (Executive):**
- **E7 VP** (rank 10) - manages multiple M5/M6 Directors across different business units or functions.
- **E8 SVP** (rank 11) - oversees or manages multiple business units or functions.

**C-Level** (rank 12) - Executive Officers of the company (CTO, CFO, COO, CEO, etc.).

### The 7 framework dimensions

Every level in the framework is defined across 7 dimensions:

1. **Scope & Complexity** - from single tasks (P2) → full domain ownership (P4-P5) → company-wide (P6+, M5+) → business unit / multi-BU (E7+, C-Level)
2. **Autonomy** - from "guided by senior" (P2) → "self-directed within domain" (P4) → "sets direction for domain" (P5) → "shapes company direction" (P6, M5+, C-Level)
3. **Influence** - from "learning" (P2) → "peer influence" (P3-P4) → "cross-functional influence" (P5+, M4+) → "org-wide" (M5+, C-Level)
4. **Business Impact** - from "task completion" (P2) → "domain outcomes" (P4-P5) → "org-level KPIs" (P6+, M5+) → "company-strategic" (C-Level)
5. **Leadership/Mentorship** - for P-track: mentoring peers/juniors (increases with rank); for M-track: managing people (M3+); for C-Level: setting culture and org design
6. **Communication** - from reporting status and asking questions (P1-P2) → leading technical discussions (P4) → executive and cross-department negotiation (P6, M5+) → board, investor and public narrative (E8, C-Level)
7. **Engineering Culture** - **R&D job families only.** Ignore this dimension entirely when leveling non-R&D roles; it is an additional scope consideration, not a requirement every role must satisfy.

When reading a resume, mentally score each role against each of the applicable dimensions (6 for most roles, 7 for R&D) and land on the level that best fits. Don't rely on title alone.

### Title traps

The framework carries a `title_traps` array on every level, listing the title strings that route to the wrong level if the anchor table is trusted without reading the bullets. Read them. Two rules generalize across the whole file:

- **Industry beats title at E7 and above.** "VP", "SVP", "Managing Director", "Director" and "Executive Director" denote materially different levels in banking, professional services, nonprofits and Commonwealth-jurisdiction companies than they do at a technology company. A resume with "VP" at an investment bank and "VP" at a SaaS company holds two genuinely different levels - only `industry` distinguishes them. Where industry is unclear on an executive-titled role, ask rather than guess.
- **"Head of X" carries no level information on its own.** It appears at P4 (sole practitioner), M4 (with reports), M6 (multi-department) and E7 (company-wide). What reports up decides it.

### Common audit mistakes

- **Auto-assigning M4 from "Manager" titles**: see the **Decision tree for "Manager"-titled roles** above. Always read bullets for hire/fire/budget evidence; if neither managerial nor supervisory duties are explicit, assume P4 Senior (IC). Titles like "Social and Administration Manager" at services firms are typically IC scope despite the label.
- **Over-leveling Manager titles to M5**: a "Manager" who manages ICs directly (no M3 layer below) is M4, not M5. M5 requires Team Leads reporting up.
- **Read the verbs in bullets carefully** ("led" vs "supported" vs "designed and delivered"). A role's level can move up (P4→P5) based on explicit "Led ..." verbs + initiative ownership. A role's level can move down (P5→P4) if closer reading shows "designed and delivered curriculum" + "guided future professionals" is *teaching*, not *leading a program*. Pattern: do a first pass from titles, then a second pass reading actual verbs in bullets, then a third pass against framework dimension language.
- **Title-anchor first pass can mislead in both directions** - over-level title-flavored ICs (the Manager-title pattern) *and* under-level subject-matter-expert teaching/mentoring roles. Be ready to revisit calls after seeing fuller context (interview notes, LinkedIn-augmentation passes).
- **Over-leveling Sr X Business Partner to P6**: P6 requires *company-wide* functional authority. A senior partner serving one business unit at a large company is P5, not P6.
- **Forgetting the M-track requires actual management**: a "Founder/Director" title with bullets describing solo IC work is P-track, not M-track. The framework draws the line at "manages people".
- **Under-applying C-Level for real Executive Officers**: a CTO of a small company with 20 reports across multiple sub-functions is still C-Level by title-anchor and by being a real Executive Officer.
- **Founder/CEO bullets that read as pure product/functional work, not GM work (NEW 2026-07-19)**: when a Founder/Co-Founder/CEO role's bullets describe only product-ownership, technical, or functional-delivery work (e.g. "wrote requirements," "managed MVP launch," "managed product development through three releases") with NO bullets on P&L, fundraising, sales, or company-wide operations, weight `family_tags` by the literal bullet content (e.g. Product Management dominant) rather than assuming General Management dominance from the title alone - the title still earns a meaningful secondary weight, but shouldn't win by default. **This is one of the highest-leverage borderline calls to surface to the user**: it can flip which professional sphere ranks #1 in `aggregates.professional_spheres_ranked_by_dominant` for the whole candidate, especially when it's their longest-tenured role. Confirmed via a real-world test parse (a Co-Founder/CEO role at a small product company): user-confirmed product-management-dominant weighting made Product Management the #1 sphere ahead of HR/TA, contradicting the candidate's own self-described "HR and Talent Acquisition executive" framing - surface this kind of contradiction explicitly rather than silently resolving it.
- **Country Manager / general-management roles with direct (not layered) department management**: a "Country Manager" (or similar P&L-owning general-management title) who directly manages multiple functional departments (sales, marketing, recruiting, finance, HR) without an intermediate Director layer beneath them can still land at M6 Senior Director if they hold full P&L/legal-entity ownership and cross-functional budget/strategy authority - even though M6's textbook definition assumes "manages Managers (M4)." Flag this as a borderline call in `data_quality` since the org-shape doesn't match the textbook M6 pattern exactly, but the P&L/entity scope justifies the level. Confirmed via a real-world test parse (a Country Manager role with full P&L ownership over sales, marketing, recruiting, and finance).

## Job family taxonomy

Source: `reference-data/job-families-and-industries.json` (taxonomy **v2.0** as of 2026-07-19).

### Family assignment

Each role gets multi-tag `family_tags` with weights summing to 1.0 across all families. Weights roll up to family-level shares.

A role can mix families. Example: "HR Business Partner / Operations Manager" might be 0.7 Human Resources & People Operations + 0.3 General Management & Exec.

Always record both family weights AND the per-family `job_types` breakdown, with reasoning for each.

### HR / TA / People Ops split (unaffected by the v2.0 taxonomy restructuring)

The `human_resources` and `talent_acquisition` families are **siblings**, not nested. Distinguishing them is important because hiring managers care about whether someone's career is recruitment-heavy or HR-Operations-heavy.

| Family | Covers | Job types include |
|---|---|---|
| **`human_resources`** (HR & People Operations) | Employee lifecycle from hire-acceptance onward | HR Generalist, HRBP, HR Operations, comp/benefits, HRIS, L&D, OD, DEI, employee relations, immigration, onboarding, engagement, performance management, policy/compliance |
| **`talent_acquisition`** (TA & Recruitment) | Pre-hire pipeline ownership | Recruiter, Sourcer, TA Partner, TA Operations/Manager/Director, RPO Recruiter, employer branding (recruitment), candidate experience |

**Default tagging heuristics:**
- "HR Generalist" / "HR Manager" / "HRBP" titles → primarily `human_resources` with `talent_acquisition` as a non-dominant secondary weight if bullets describe recruitment work
- "Recruiter" / "TA Partner" / "Recruitment Manager" / "Recruitment Consultant" titles → primarily `talent_acquisition`
- Mixed titles like "Global TA and HR Programs Manager" → weight by bullet content; if 50/50, nudge slightly toward HR/People Ops dominance to reflect the broader HR-track career path

This split lets the visualization surface TA as a distinct sphere (its own color) on candidates where recruitment is a meaningful career thread, even when not dominant.

### Industry assignment

Single-valued per role. If the company spans industries, pick the closer fit and note the alternative in reasoning.

**Taxonomy gap handling (precedent set 2026-07-19)**: if no existing industry or job_type fits, add a new one directly to `reference-data/job-families-and-industries.json` (industries can be added without a version bump; job_types likewise don't require one) rather than force-fitting to an imperfect neighbor. Always flag the addition in `data_quality` with the reasoning for why existing options didn't fit. Precedents already in the taxonomy from a real-world test parse: industry `agriculture_food_manufacturing` (multi-industry agroholding - agriculture, meat processing, FMCG wholesale; none of `industrial_iot`/`retail`/others fit) and job_type `consumer_retail_sales` under the `sales` family (entry-level auto dealership sales; none of `enterprise_sales`/`account_management`/`business_development` fit).

### Professional spheres - roll-up from per-role weights to candidate ranking

The per-role `family_tags` array describes the **role's** professional sphere composition. The `aggregates.professional_spheres_ranked_by_dominant` array describes the **candidate's** career sphere ranking. These are computed by aggregation, not stored independently.

**Aggregation rule: months-where-dominant.** For each role, identify the dominant family (highest weight in `family_tags`; first-listed wins on exact tie). Credit that role's `duration_months` to its dominant family. Sum across all on-chart roles; rank families by total months descending. This is the candidate-level sphere ranking.

**Off-chart roles** (where `render_policy.on_chart === false`) do NOT contribute to the sphere ranking. They still get full per-role `family_tags` in JSON for completeness, but the chart's sphere palette and legend only reflect on-chart roles.

**Why dominance-by-role, not weight-sum?** A role mostly about teaching (Education 0.7, TA 0.3) contributes to the Education count, not split fractionally. This matches the human intuition that "she taught for 7 years" is more meaningful than "she taught with 5 hours/week of TA tasks mixed in." The secondary weight (TA 0.3) still surfaces visually as a stripe on the role's bar - it's not lost, just not credited to the sphere ranking.

**Ties** in months-where-dominant: alphabetical by family_id is the deterministic fallback. In practice, ranks 1-3 are usually unambiguous; tie-breaking matters only for tail-end spheres.

**Multi-family roles** - when to use:
- Single-family (weight 1.0): one family covers everything in the role. Default for purely-focused roles (HR Generalist, Engineer, Designer).
- Two families: when the role has a true sub-focus or split. Examples: "HR & Operations Assistant" = HR 0.6 + Admin/Office 0.4 (dual-title role); "Global TA and HR Programs Manager" = HR 0.55 + TA 0.45.
- Three+ families: rare; reserved for genuinely multi-functional roles where dropping any family would misrepresent the work.

**Sphere palette assignment** is downstream (the visualization skill assigns rank → color). At parsing time, just compute the ranking correctly; don't worry about color.

## Schema (v1.0)

```json
{
  "$schema_version": "1.0",
  "generated": "YYYY-MM-DD",
  "source": "filename.pdf (uploaded resume, treated as sole source of truth)",
  "taxonomy_source": "job-families-and-industries.json v2.0",

  "candidate": {
    "name": "Full Name",
    "contact": {
      "phone": "+... or null",
      "email": "name@... or null",
      "linkedin": "https://linkedin.com/in/... or null",
      "github": "... or null",
      "portfolio": "... or null",
      "location": "City, Country (verbatim from resume)",
      "relocation": "null unless source resume states it",
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
      "company_history_note": "Optional italic line under company for renames/entity relationships",
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
      "narrative_source_note": "Optional; captures LinkedIn-augmented bullets etc.",

      "strata": {
        "code": "M5",
        "name": "Director",
        "rank": 8,
        "reasoning": "Explicit reasoning for the level assignment, referencing bullet language and framework dimensions."
      },

      "family_tags": [
        {
          "family_id": "human_resources",
          "family_name": "Human Resources & People Operations",
          "weight": 0.7,
          "job_types": [
            { "id": "hr_business_partner", "weight": 0.5, "reasoning": "..." },
            { "id": "hr_operations", "weight": 0.2, "reasoning": "..." }
          ],
          "reasoning": "Why this family and this weight."
        }
      ],

      "industry": {
        "id": "technology_software",
        "name": "Technology & Software",
        "reasoning": "..."
      },

      "role_type": {
        "value": "IC | People Manager",
        "reasoning": "IC/PM flag reflects team-leadership, separate from strata level."
      },

      "render_policy": {
        "on_chart": true,
        "in_experience_text": true,
        "exclusion_reason": "Only populated if on_chart is false."
      },

      "connector": {
        "same_employer_as_previous": true,
        "move_type_from_previous": "promotion | lateral | company_change | role_change | side_gig_start",
        "previous_role_id": "role_2",
        "notes": "Optional context."
      }
    }
  ],

  "internships": [ /* same shape as roles, optional */ ],

  "aggregates": {
    "career_start": "YYYY-MM",
    "career_end": "YYYY-MM or 'current (YYYY-MM)'",
    "career_length_months": 121,
    "career_length_label": "10 years 1 month",
    "sum_of_tenure_months": 113,
    "sum_of_tenure_label": "9 years 5 months",
    "overlap_months": 0,
    "gaps": [{ "from": "YYYY-MM", "to": "YYYY-MM", "months": N, "note": "..." }],
    "role_count": 5,
    "role_count_on_chart": 5,
    "role_count_off_chart": 0,
    "employer_count": 4,
    "peak_strata": { "code": "M5", "name": "Director", "rank": 8 },
    "strata_trajectory": [
      { "role_id": "role_X", "code": "P3", "rank": 2, "year": 2019, "company": "..." }
    ],
    "professional_spheres_ranked_by_dominant": [
      {
        "rank": 1,
        "color": "#75a426",
        "family_id": "human_resources",
        "family_name": "Human Resources & People Operations",
        "months": 113,
        "months_label": "9 years 5 months",
        "share_of_sum_pct": 100.0,
        "roles_where_dominant": ["role_1", "role_2"],
        "note": "..."
      }
    ]
  },

  "data_quality": [
    {
      "field": "roles[role_1].strata",
      "severity": "advisory | informational",
      "note": "Explanation of any borderline call, revision history, or user override."
    }
  ]
}
```

## Content rules (LOCKED - these flow downstream)

1. **Bullets are captured verbatim**. Never paraphrase, reword, combine, drop "etc.", or truncate. If bullets are LinkedIn-augmented (not from the resume PDF), note the source per role via `narrative_source_note`.
2. **Education dates are NEVER captured** even if the source resume includes them. Protects candidates from age-based screening downstream.
3. **Location** captured verbatim from source; do NOT infer country if not stated.
4. **Summary paragraph** captured verbatim if present. The renderer does NOT render this - it's kept in JSON for downstream consumers (job-matching, search).
5. **Section conservatism**: capture Languages, Top Skills, Personal Characteristics, Interests, Driver's License, References in JSON if present, but flag in `data_quality` that they should NOT render by default.
6. **Audit trail is mandatory** for every borderline strata call. Include the reasoning chain in `strata.reasoning` and a `data_quality` entry if the call was revised or overridden.

## Edge cases

### Group date brackets
Some resumes list multiple roles under one date range: "Company X, 2018-2020: Role A, Role B, Role C". Parse each as separate role with `is_estimated: true` and best-effort start/end month inference. Mark in `data_quality`.

### Missing dates
If a role has no dates at all: skip it, or (if user wants) infer from context (e.g. positioned between two dated roles) with `is_estimated: true` and low-confidence data_quality flag. Prefer skipping.

### Single-sentence roles
Common for old / brief / entry-level roles. Set `single_sentence: true`. The renderer will render solid bars (no multi-family stripes) since there's not enough data to infer a breakdown.

### Concurrent roles
Two genuinely concurrent roles (e.g. part-time + full-time, or contractor at company A while employed at company B) → both get their own entries with overlapping date ranges. Note the overlap in `aggregates.overlap_months` and add a `data_quality` flag.

**On-chart vs off-chart decision for side gigs**: when a side gig overlaps with a main career role, decide based on whether including it tells a clearer career story:
- **Include on-chart** if it represents a genuine career thread, even small (e.g. a 2y9m senior-IC teaching side gig parallel to an HR career). The lane-split logic in the renderer will visually disambiguate.
- **Include on-chart** also for short side gigs in a different sphere if it adds biographical context (e.g. Fitness Instructor parallel to Kindergarten Teacher - both on-chart, lane-split at same rank during overlap).
- **Off-chart** only for genuinely tangential work (e.g. a few months of freelance gigs unrelated to the career arc).

The user makes the final call - surface borderline decisions per the workflow's Step 3.

### Off-chart pre-career roles
Pre-HR / pre-career roles at companies in different professional families (Sales Support, Receptionist, Event Hostess) → `render_policy.on_chart = false`. They appear in the textual Experience section but not on the ladder chart. The chart axis spans only the **on-chart** career.

**Counter-example**: when the user wants a maximal-history view (all career steps on chart), even pre-career roles in different families can be on-chart. A candidate whose final chart has all 9 roles on-chart including 7 years of Kindergarten Teacher (a different sphere from her HR career) is a legitimate user choice. Default is off-chart for different-family pre-career; be ready to flip.

### Very old / brief roles
Roles from more than 10-15 years ago that don't inform the current career picture may be off-chart. Case-by-case; ask user.

## LinkedIn augmentation

When a candidate provides both a resume PDF AND a LinkedIn export/profile:
1. **Resume is canonical for dates and bullet content.** Never overwrite resume-sourced content with LinkedIn-sourced content.
2. **LinkedIn is additive**: it can add roles the resume omitted (side gigs, brief roles), fuller bullet descriptions for existing roles, and context (like same-employer entity relationships).
3. Every LinkedIn-sourced piece gets a provenance note: `narrative_source_note` on the role, `linkedin_source_note` on the contact field, or a `data_quality` entry describing the augmentation pass.
4. Bump the JSON's `data_quality` with a "_meta" entry describing what was added.

## Output

Save to a working file location. Always include a data_quality section flagging any borderline calls, revisions, or user overrides - even if the JSON was clean, the empty audit trail is itself a signal.

**Then validate before handing off to Phase 2:**

```
python3 scripts/validate_structured_json.py path/to/structured.json
```

Exit code 0 means the contract holds; exit 1 means Phase 2 would render incorrectly. Fix every ERROR before rendering and review the WARNs. The validator catches the failure modes that are tedious to eyeball - family weights that do not sum to 1.0, a `strata.code`/`rank` pair that disagrees with the framework, aggregates that drifted after a late strata revision, a dominant family with no ranked sphere entry (a bar with no colour), a dangling `connector.previous_role_id`, and any education date that crept in against the LOCKED content rule.

It is a check on arithmetic and cross-references only. It cannot tell you whether a leveling call is *right* - that still needs the user sign-off described in Step 3.

`reference-data/example-structured.json` is a small synthetic fixture (fabricated candidate, not a real resume) showing a complete, valid document. Consult it when unsure how a field is meant to be populated.

## Versioning & contract stability

- The JSON schema version is currently `1.0`. Field additions that don't break existing consumers are OK to add without a bump.
- The taxonomy version is currently `2.0` (2026-07-19, full restructuring to 34 families anchored on O*NET-SOC's public major groups). Bump if a family is split, merged, or removed. Add new families/industries without a bump.
- The visualization phase (`reference/visualization.md`) and any future skill (e.g. `resume-job-matching`) should tolerate additive schema changes and fail loudly on missing required fields.
