#!/usr/bin/env python3
"""
test_validator.py - self-test for validate_structured_json.py.

Takes the bundled synthetic example, breaks it in one specific way at a time, and
asserts the validator produces an ERROR at the expected path. Also asserts the
unmodified example stays clean, which is what stops the fixture from silently
rotting when the schema or reference data changes.

Run:  python3 scripts/test_validator.py
Exit: 0 all pass, 1 any failure.

Standard library only.
"""

import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from validate_structured_json import validate  # noqa: E402

EXAMPLE = os.path.join(SKILL, "reference-data", "example-structured.json")
REF_DIR = os.path.join(SKILL, "reference-data")


def mutations(base):
    """(label, mutated_doc, expected_error_path_prefix) triples."""
    out = []

    def m(label, path_prefix, fn):
        d = copy.deepcopy(base)
        fn(d)
        out.append((label, d, path_prefix))

    def set_rank(d):
        d["roles"][0]["strata"]["rank"] = 8

    def bad_weight(d):
        d["roles"][0]["family_tags"][0]["weight"] = 0.9

    def bad_family(d):
        d["roles"][0]["family_tags"][0]["family_id"] = "data_analytics"

    def edu_date(d):
        d["candidate"]["education"][0]["graduation_year"] = 2015

    def bad_peak(d):
        d["aggregates"]["peak_strata"]["rank"] = 3

    def dupe_ids(d):
        d["roles"][1]["id"] = d["roles"][0]["id"]

    def dangling_connector(d):
        d["roles"][0]["connector"]["previous_role_id"] = "role_99"

    def drop_sphere(d):
        d["aggregates"]["professional_spheres_ranked_by_dominant"].pop(1)

    def backwards_dates(d):
        d["roles"][0]["end_date"] = "2018-01"

    def unsorted_spheres(d):
        d["aggregates"]["professional_spheres_ranked_by_dominant"].reverse()

    def nothing_on_chart(d):
        for r in d["roles"]:
            r["render_policy"]["on_chart"] = False

    def no_strata(d):
        del d["roles"][0]["strata"]

    def bad_rank_range(d):
        d["roles"][0]["strata"]["rank"] = 13

    def bad_role_count(d):
        d["aggregates"]["role_count"] = 99

    def no_bullets(d):
        d["roles"][0]["narrative_bullets"] = []

    m("strata rank contradicts framework code", "roles[role_1].strata", set_rank)
    m("family weights do not sum to 1", "roles[role_1].family_tags", bad_weight)
    m("family_id absent from taxonomy", "roles[role_1].family_tags[0].family_id", bad_family)
    m("education date captured", "candidate.education[0].graduation_year", edu_date)
    m("peak_strata disagrees with roles", "aggregates.peak_strata.rank", bad_peak)
    m("duplicate role ids", "roles", dupe_ids)
    m("connector references missing role", "roles[role_1].connector.previous_role_id",
      dangling_connector)
    m("dominant family has no ranked sphere", "aggregates.professional_spheres", drop_sphere)
    m("end_date precedes start_date", "roles[role_1]", backwards_dates)
    m("spheres not sorted by months desc", "aggregates.professional_spheres", unsorted_spheres)
    m("no on-chart roles", "aggregates.role_count_on_chart", nothing_on_chart)
    m("role missing strata", "roles[role_1].strata", no_strata)
    m("rank outside frozen 0-12 contract", "roles[role_1].strata.rank", bad_rank_range)
    m("aggregates.role_count wrong", "aggregates.role_count", bad_role_count)
    m("role has no bullets", "roles[role_1].narrative_bullets", no_bullets)
    return out


def main():
    try:
        with open(EXAMPLE) as f:
            base = json.load(f)
    except Exception as e:
        print("could not load fixture %s: %s" % (EXAMPLE, e))
        return 1

    failures = []

    rep = validate(base, REF_DIR)
    if rep.errors:
        failures.append("unmodified example produced %d error(s): %s"
                        % (len(rep.errors), rep.errors[0]))
        print("FAIL  unmodified example should validate clean")
    else:
        print("ok    unmodified example validates clean (%d warnings)" % len(rep.warns))

    for label, doc, expected in mutations(base):
        rep = validate(doc, REF_DIR)
        hit = [e for e in rep.errors if e["path"].startswith(expected)]
        if hit:
            print("ok    %s" % label)
        else:
            print("FAIL  %s -> expected ERROR at %r, got %s"
                  % (label, expected, [e["path"] for e in rep.errors] or "no errors"))
            failures.append(label)

    print()
    if failures:
        print("%d failure(s)" % len(failures))
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
