#!/usr/bin/env python3
"""
validate_structured_json.py - contract checker for the resume-parsing-visualization skill.

Validates a Phase 1 `structured.json` against JSON schema v1.0, and cross-checks it
against the skill's reference data (leveling-framework.json, job-families-and-industries.json).

This exists because the schema is the contract between Phase 1 (parsing) and Phase 2
(rendering), and "fail loudly if a required field is missing" was previously only a
prose instruction. Run this between the two phases.

Usage
-----
    python3 scripts/validate_structured_json.py path/to/structured.json
    python3 scripts/validate_structured_json.py structured.json --strict
    python3 scripts/validate_structured_json.py structured.json --reference-data path/to/reference-data
    python3 scripts/validate_structured_json.py structured.json --json

Exit codes
----------
    0  no errors (warnings may be present, unless --strict)
    1  one or more ERRORs found (or WARNs with --strict)
    2  could not read/parse the input file

Severity
--------
    ERROR  Phase 2 will render wrong or crash. Fix before rendering.
    WARN   Probably a mistake, but renderable. Review before shipping.

No third-party dependencies - standard library only.
"""

import argparse
import json
import os
import re
import sys
from datetime import date

SCHEMA_VERSION = "1.0"
RANK_MIN, RANK_MAX = 0, 12
DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
WEIGHT_TOL = 0.01
DURATION_TOL = 1  # months

# Education keys that must never be populated (age-screening protection).
# Matched as a substring pattern, not an exact set: `graduation_year`, `yearAwarded`
# and `completion_date` are all the same violation as a bare `year`, and an exact-match
# list only catches the spellings someone happened to think of.
FORBIDDEN_EDUCATION_KEY_RE = re.compile(
    r"(date|year|graduat|complet|award|conferr|attend|start|end|from|to|period|since|until)",
    re.IGNORECASE,
)

# Keys that contain a forbidden substring but are legitimately about the qualification
# itself rather than when it happened.
EDUCATION_KEY_ALLOWLIST = {"field", "field_of_study"}

# Sections captured in JSON but never rendered by default.
CONSERVATIVE_SECTIONS = [
    "languages", "top_skills", "personal_characteristics",
    "interests", "drivers_license", "references",
]


class Report:
    def __init__(self):
        self.errors = []
        self.warns = []
        self.checks = 0

    def error(self, path, msg):
        self.errors.append({"severity": "ERROR", "path": path, "message": msg})

    def warn(self, path, msg):
        self.warns.append({"severity": "WARN", "path": path, "message": msg})

    def ok(self):
        self.checks += 1


# ---------------------------------------------------------------- helpers

def months_between(start, end):
    """Inclusive month count between YYYY-MM strings, matching duration_months semantics."""
    sy, sm = int(start[:4]), int(start[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    return (ey - sy) * 12 + (em - sm) + 1


def today_ym():
    t = date.today()
    return "%04d-%02d" % (t.year, t.month)


def as_of_ym(doc):
    """
    The reference 'now' for open-ended roles.

    `duration_months` on a current role was computed when the file was generated, so an
    older file must be checked against its own `generated` date - otherwise every stored
    JSON starts emitting spurious duration warnings as the wall clock moves on.
    """
    gen = doc.get("generated")
    if isinstance(gen, str) and re.match(r"^\d{4}-\d{2}", gen):
        return gen[:7]
    return today_ym()


def resolve_end(role, as_of):
    """Return a concrete YYYY-MM for a role's end, or None if unparseable."""
    end = role.get("end_date")
    if end == "current":
        return as_of
    if isinstance(end, str) and DATE_RE.match(end):
        return end
    return None


def get(d, key, default=None):
    return d.get(key, default) if isinstance(d, dict) else default


def load_reference_data(ref_dir, rep):
    """Load leveling framework + taxonomy. Missing files downgrade to warnings."""
    levels, families, job_types, industries = None, None, None, None

    lvl_path = os.path.join(ref_dir, "leveling-framework.json")
    tax_path = os.path.join(ref_dir, "job-families-and-industries.json")

    try:
        with open(lvl_path) as f:
            lf = json.load(f)
        levels = {l["code"]: l for l in lf.get("levels", [])}
    except Exception as e:
        rep.warn("_reference_data",
                 "could not load %s (%s) - skipping strata cross-checks" % (lvl_path, e))

    try:
        with open(tax_path) as f:
            tx = json.load(f)
        families = {fam["id"]: fam for fam in tx.get("job_families", [])}
        job_types = {
            fam["id"]: {jt["id"] for jt in fam.get("job_types", [])}
            for fam in tx.get("job_families", [])
        }
        industries = {ind["id"] for ind in tx.get("industries", [])}
    except Exception as e:
        rep.warn("_reference_data",
                 "could not load %s (%s) - skipping taxonomy cross-checks" % (tax_path, e))

    return levels, families, job_types, industries


# ---------------------------------------------------------------- checks

def check_envelope(doc, rep):
    ver = doc.get("$schema_version")
    if ver is None:
        rep.error("$schema_version", "missing - Phase 2 checks this before rendering")
    elif ver != SCHEMA_VERSION:
        rep.warn("$schema_version",
                 "is %r, this validator targets %r - additive changes are fine, "
                 "breaking ones need a synchronized Phase 2 update" % (ver, SCHEMA_VERSION))
    else:
        rep.ok()

    if not doc.get("taxonomy_source"):
        rep.warn("taxonomy_source", "missing - Phase 2's workflow step 1 expects it")

    if not get(doc.get("candidate", {}), "name"):
        rep.error("candidate.name", "missing or empty - required for the hero block")
    else:
        rep.ok()


def check_education_dates(doc, rep):
    """LOCKED content rule: education dates are never captured or rendered."""
    edu = get(doc.get("candidate", {}), "education") or []
    for i, e in enumerate(edu):
        if not isinstance(e, dict):
            rep.error("candidate.education[%d]" % i, "expected an object")
            continue
        for k, v in e.items():
            if k.lower() in EDUCATION_KEY_ALLOWLIST:
                continue
            if FORBIDDEN_EDUCATION_KEY_RE.search(k) and v not in (None, "", []):
                rep.error(
                    "candidate.education[%d].%s" % (i, k),
                    "education dates must never be captured (age-screening protection); "
                    "found %r" % (v,),
                )
        rep.ok()


def check_conservative_sections(doc, rep):
    cand = doc.get("candidate", {})
    flagged = " ".join(
        str(q.get("field", "")) + " " + str(q.get("note", ""))
        for q in (doc.get("data_quality") or [])
    ).lower()
    for sec in CONSERVATIVE_SECTIONS:
        if cand.get(sec) and sec not in flagged:
            rep.warn(
                "candidate.%s" % sec,
                "populated but not flagged in data_quality; section conservatism says it "
                "must not render by default - add a data_quality note so Phase 2 knows",
            )


def check_role(role, i, ids, levels, families, job_types, industries, rep, as_of):
    p = "roles[%d]" % i
    rid = role.get("id")
    if rid:
        p = "roles[%s]" % rid

    for field in ("id", "company", "title", "start_date", "end_date", "duration_months"):
        if role.get(field) in (None, ""):
            rep.error("%s.%s" % (p, field), "required field missing or empty")

    # --- dates
    start = role.get("start_date")
    if isinstance(start, str) and not DATE_RE.match(start):
        rep.error("%s.start_date" % p, "expected YYYY-MM, got %r" % start)
    end_raw = role.get("end_date")
    if isinstance(end_raw, str) and end_raw != "current" and not DATE_RE.match(end_raw):
        rep.error("%s.end_date" % p, "expected YYYY-MM or 'current', got %r" % end_raw)

    end = resolve_end(role, as_of)
    if isinstance(start, str) and DATE_RE.match(start) and end:
        if end < start:
            rep.error("%s" % p, "end_date %r precedes start_date %r" % (end_raw, start))
        else:
            rep.ok()
            computed = months_between(start, end)
            dm = role.get("duration_months")
            if isinstance(dm, int) and abs(dm - computed) > DURATION_TOL:
                rep.warn(
                    "%s.duration_months" % p,
                    "is %d but dates %s..%s imply ~%d - bar width is drawn from the dates, "
                    "so the tenure header and the chart will disagree" % (dm, start, end_raw, computed),
                )

    is_current = role.get("is_current")
    if is_current is True and end_raw != "current":
        rep.error("%s.is_current" % p, "true but end_date is %r" % end_raw)
    if end_raw == "current" and is_current is not True:
        rep.error("%s.is_current" % p, "end_date is 'current' but is_current is %r" % is_current)

    # --- bullets
    bullets = role.get("narrative_bullets")
    if not isinstance(bullets, list) or not bullets:
        rep.error("%s.narrative_bullets" % p, "missing or empty - the textual half renders from this")
    else:
        rep.ok()
        if role.get("single_sentence") is True and len(bullets) > 1:
            rep.warn("%s.single_sentence" % p,
                     "true but there are %d bullets" % len(bullets))

    # --- strata
    st = role.get("strata")
    if not isinstance(st, dict):
        rep.error("%s.strata" % p, "missing - Phase 2 fails loudly without it")
    else:
        code, name, rank = st.get("code"), st.get("name"), st.get("rank")
        if not isinstance(rank, int):
            rep.error("%s.strata.rank" % p, "must be an integer, got %r" % (rank,))
        elif not (RANK_MIN <= rank <= RANK_MAX):
            rep.error("%s.strata.rank" % p,
                      "%d is outside the frozen rank contract %d-%d" % (rank, RANK_MIN, RANK_MAX))
        else:
            rep.ok()
        if levels is not None:
            lv = levels.get(code)
            if lv is None:
                rep.error("%s.strata.code" % p,
                          "%r is not a level in leveling-framework.json (valid: %s)"
                          % (code, ", ".join(sorted(levels))))
            else:
                if lv.get("rank") != rank:
                    rep.error("%s.strata" % p,
                              "code %s is rank %s in the framework but this role says rank %r"
                              % (code, lv.get("rank"), rank))
                if name != lv.get("name"):
                    rep.warn("%s.strata.name" % p,
                             "is %r but the framework calls %s %r" % (name, code, lv.get("name")))
        if not st.get("reasoning"):
            rep.warn("%s.strata.reasoning" % p,
                     "empty - the audit trail is mandatory for every strata call")

    # --- family tags
    tags = role.get("family_tags")
    if not isinstance(tags, list) or not tags:
        rep.error("%s.family_tags" % p, "missing or empty - bar color is derived from this")
    else:
        rep.ok()
        total = 0.0
        for j, t in enumerate(tags):
            tp = "%s.family_tags[%d]" % (p, j)
            if not isinstance(t, dict):
                rep.error(tp, "expected an object")
                continue
            w = t.get("weight")
            if not isinstance(w, (int, float)):
                rep.error("%s.weight" % tp, "must be a number, got %r" % (w,))
            else:
                total += float(w)
                if not (0 < w <= 1):
                    rep.error("%s.weight" % tp, "%r is outside (0, 1]" % w)
            fid = t.get("family_id")
            if families is not None and fid not in families:
                rep.error("%s.family_id" % tp,
                          "%r is not in job-families-and-industries.json" % fid)
            elif families is not None and t.get("family_name") != families[fid]["name"]:
                rep.warn("%s.family_name" % tp,
                         "is %r but the taxonomy calls %s %r"
                         % (t.get("family_name"), fid, families[fid]["name"]))
            if job_types is not None and fid in job_types:
                jt_total = 0.0
                for jt in t.get("job_types") or []:
                    if jt.get("id") not in job_types[fid]:
                        rep.warn("%s.job_types" % tp,
                                 "%r is not a job_type of family %s" % (jt.get("id"), fid))
                    if isinstance(jt.get("weight"), (int, float)):
                        jt_total += float(jt["weight"])
                if (t.get("job_types") and isinstance(w, (int, float))
                        and abs(jt_total - w) > WEIGHT_TOL):
                    rep.warn("%s.job_types" % tp,
                             "weights sum to %.3f but the family weight is %.3f" % (jt_total, w))
        if abs(total - 1.0) > WEIGHT_TOL:
            rep.error("%s.family_tags" % p,
                      "weights sum to %.3f, expected 1.0 - sphere months roll up from these" % total)
        else:
            rep.ok()

    # --- industry
    ind = role.get("industry")
    if industries is not None and isinstance(ind, dict):
        if ind.get("id") not in industries:
            rep.warn("%s.industry.id" % p, "%r is not in the taxonomy" % ind.get("id"))

    # --- render policy
    rp = role.get("render_policy")
    if not isinstance(rp, dict):
        rep.error("%s.render_policy" % p, "missing - Phase 2 needs on_chart / in_experience_text")
    else:
        if not isinstance(rp.get("on_chart"), bool):
            rep.error("%s.render_policy.on_chart" % p, "must be a boolean")
        if not isinstance(rp.get("in_experience_text"), bool):
            rep.error("%s.render_policy.in_experience_text" % p, "must be a boolean")
        if rp.get("on_chart") is False and not rp.get("exclusion_reason"):
            rep.warn("%s.render_policy.exclusion_reason" % p,
                     "off-chart role with no stated reason")
        if rp.get("on_chart") is False and rp.get("in_experience_text") is False:
            rep.warn(p, "neither on the chart nor in the experience text - role renders nowhere")

    # --- connector
    con = role.get("connector")
    if isinstance(con, dict) and con.get("previous_role_id"):
        if con["previous_role_id"] not in ids:
            rep.error("%s.connector.previous_role_id" % p,
                      "%r does not match any role id" % con["previous_role_id"])


def check_aggregates(doc, rep, families):
    agg = doc.get("aggregates")
    if not isinstance(agg, dict):
        rep.error("aggregates", "missing - the tenure header and sphere palette read from it")
        return

    roles = doc.get("roles") or []
    on_chart = [r for r in roles if get(r.get("render_policy", {}), "on_chart") is True]

    if agg.get("role_count") != len(roles):
        rep.error("aggregates.role_count",
                  "is %r but there are %d roles" % (agg.get("role_count"), len(roles)))
    if "role_count_on_chart" in agg and agg["role_count_on_chart"] != len(on_chart):
        rep.error("aggregates.role_count_on_chart",
                  "is %r but %d roles have on_chart true"
                  % (agg["role_count_on_chart"], len(on_chart)))
    employers = {r.get("company") for r in roles if r.get("company")}
    if "employer_count" in agg and agg["employer_count"] != len(employers):
        rep.warn("aggregates.employer_count",
                 "is %r but there are %d distinct company values - check for spelling "
                 "variants, which would also split the same-employer staircase"
                 % (agg["employer_count"], len(employers)))

    if not on_chart:
        rep.error("roles", "no role has render_policy.on_chart true - the chart would be empty")
        return
    rep.ok()

    ranks = [get(r.get("strata", {}), "rank") for r in on_chart]
    ranks = [x for x in ranks if isinstance(x, int)]
    if ranks:
        peak = agg.get("peak_strata") or {}
        if peak.get("rank") != max(ranks):
            rep.error("aggregates.peak_strata.rank",
                      "is %r but the highest on-chart role rank is %d"
                      % (peak.get("rank"), max(ranks)))
        else:
            rep.ok()
        if min(ranks) == RANK_MIN:
            rep.warn("aggregates",
                     "chart floor is rank 0 (P1) - confirm the renderer computes band index as "
                     "`rank - floorRank`, not `rank - 1` (see visualization spec 5.3)")

    # --- sphere ranking
    spheres = agg.get("professional_spheres_ranked_by_dominant")
    if not isinstance(spheres, list) or not spheres:
        rep.error("aggregates.professional_spheres_ranked_by_dominant",
                  "missing or empty - Phase 2 builds the color palette from it")
        return
    rep.ok()

    expected_ranks = list(range(1, len(spheres) + 1))
    if [s.get("rank") for s in spheres] != expected_ranks:
        rep.error("aggregates.professional_spheres_ranked_by_dominant",
                  "ranks must be contiguous 1..%d in order, got %s"
                  % (len(spheres), [s.get("rank") for s in spheres]))
    months = [s.get("months") for s in spheres if isinstance(s.get("months"), int)]
    if months != sorted(months, reverse=True):
        rep.error("aggregates.professional_spheres_ranked_by_dominant",
                  "not sorted by months descending: %s" % months)

    ids = {r.get("id") for r in roles}
    listed_ids = set()
    for s in spheres:
        if families is not None and s.get("family_id") not in families:
            rep.error("aggregates.professional_spheres_ranked_by_dominant",
                      "family_id %r is not in the taxonomy" % s.get("family_id"))
        for rid in s.get("roles_where_dominant") or []:
            listed_ids.add(rid)
            if rid not in ids:
                rep.error("aggregates.professional_spheres_ranked_by_dominant",
                          "roles_where_dominant references unknown role id %r" % rid)

    # Every on-chart role's dominant family must be represented, or its bar has no color.
    ranked_families = {s.get("family_id") for s in spheres}
    for r in on_chart:
        tags = r.get("family_tags") or []
        if not tags:
            continue
        dom = max(tags, key=lambda t: t.get("weight", 0) if isinstance(t, dict) else 0)
        if dom.get("family_id") not in ranked_families:
            rep.error(
                "aggregates.professional_spheres_ranked_by_dominant",
                "role %r is dominant in family %r, which has no ranked sphere entry - "
                "its bar would have no palette color"
                % (r.get("id"), dom.get("family_id")),
            )


def check_data_quality(doc, rep):
    dq = doc.get("data_quality")
    if dq is None:
        rep.warn("data_quality",
                 "missing - the audit section is mandatory even when clean; an empty "
                 "audit trail is itself a signal")
    elif not isinstance(dq, list):
        rep.error("data_quality", "must be an array")
    else:
        for i, q in enumerate(dq):
            if isinstance(q, dict) and q.get("severity") not in (
                    "advisory", "informational", None):
                rep.warn("data_quality[%d].severity" % i,
                         "%r is not 'advisory' or 'informational'" % q.get("severity"))


def validate(doc, ref_dir):
    rep = Report()
    as_of = as_of_ym(doc)
    levels, families, job_types, industries = load_reference_data(ref_dir, rep)

    check_envelope(doc, rep)
    check_education_dates(doc, rep)
    check_conservative_sections(doc, rep)

    roles = doc.get("roles")
    if not isinstance(roles, list) or not roles:
        rep.error("roles", "missing or empty")
    else:
        ids = [r.get("id") for r in roles if isinstance(r, dict)]
        dupes = {x for x in ids if ids.count(x) > 1}
        if dupes:
            rep.error("roles", "duplicate role ids: %s (bar-to-article links break)"
                      % ", ".join(sorted(str(d) for d in dupes)))
        idset = set(ids)
        for i, r in enumerate(roles):
            if not isinstance(r, dict):
                rep.error("roles[%d]" % i, "expected an object")
                continue
            check_role(r, i, idset, levels, families, job_types, industries, rep, as_of)

    check_aggregates(doc, rep, families)
    check_data_quality(doc, rep)
    return rep


# ---------------------------------------------------------------- cli

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_ref = os.path.join(os.path.dirname(here), "reference-data")

    ap = argparse.ArgumentParser(description="Validate a structured.json against schema v1.0.")
    ap.add_argument("path", help="path to structured.json")
    ap.add_argument("--reference-data", default=default_ref,
                    help="directory holding leveling-framework.json and "
                         "job-families-and-industries.json (default: %(default)s)")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="emit findings as JSON")
    args = ap.parse_args()

    try:
        with open(args.path) as f:
            doc = json.load(f)
    except FileNotFoundError:
        print("could not open %s" % args.path, file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print("%s is not valid JSON: %s" % (args.path, e), file=sys.stderr)
        return 2

    rep = validate(doc, args.reference_data)
    findings = rep.errors + rep.warns

    if args.as_json:
        print(json.dumps({
            "file": args.path,
            "errors": len(rep.errors),
            "warnings": len(rep.warns),
            "findings": findings,
        }, indent=2))
    else:
        for f in findings:
            print("%-5s %s\n      %s" % (f["severity"], f["path"], f["message"]))
        if not findings:
            print("clean - %d checks passed, ready for Phase 2" % rep.checks)
        else:
            print("\n%d error(s), %d warning(s)" % (len(rep.errors), len(rep.warns)))
            if rep.errors:
                print("Phase 2 will render incorrectly until the errors are fixed.")

    if rep.errors or (args.strict and rep.warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
