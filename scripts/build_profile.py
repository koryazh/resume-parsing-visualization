#!/usr/bin/env python3
"""
Phase 2 renderer: bake a structured.json into the bundled viewer, producing the career-ladder HTML.

    python3 scripts/build_profile.py path/to/structured.json
    python3 scripts/build_profile.py path/to/structured.json -o out/Jane_Doe_career-ladder.html

The output is viewer/career-profile.html, unchanged, with the JSON placed in its
`<script type="application/json" id="profile-data">` slot. All drawing happens in the browser when the
file is opened, so no model output is spent on HTML, and every candidate's page is rendered by the
same code.

Steps, in order, each of which stops the build on failure:
  1. read the JSON
  2. run the full validator (scripts/validate_structured_json.py); any ERROR stops the build
  3. run the viewer's own minimum contract check (the fields it needs to draw)
  4. write the HTML and print the on-chart counts the page header will show

--skip-validate bypasses step 2 only, for a JSON the user has deliberately accepted with known errors.
Standard library only.
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VIEWER = ROOT / "viewer" / "career-profile.html"
REF_DIR = ROOT / "reference-data"
SLOT_RE = re.compile(r'(<script type="application/json" id="profile-data">)(.*?)(</script>)', re.S)
TITLE_RE = re.compile(r"<title>.*?</title>", re.S)
DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

sys.path.insert(0, str(HERE))
from validate_structured_json import validate  # noqa: E402


def contract_problems(doc):
    """Mirror of checkContract() in the viewer: what it needs to draw at all."""
    p = []
    if not isinstance(doc, dict):
        return ["The top level must be a JSON object."]
    ver = doc.get("$schema_version")
    if ver is not None and str(ver).split(".")[0] != "1":
        p.append("$schema_version is %s; the viewer reads schema 1.x." % ver)
    cand = doc.get("candidate")
    if not isinstance(cand, dict):
        p.append("candidate: missing.")
    elif not (isinstance(cand.get("name"), str) and cand["name"].strip()):
        p.append("candidate.name: missing.")
    roles = doc.get("roles")
    if not isinstance(roles, list) or not roles:
        p.append("roles: must be a non-empty array.")
        return p

    ids, any_on_chart = set(), False
    for i, r in enumerate(roles):
        at = "roles[%d]" % i
        if not isinstance(r, dict):
            p.append(at + ": not an object.")
            continue
        if isinstance(r.get("id"), str):
            at += " (%s)" % r["id"]
        for f in ("id", "company", "title"):
            if not (isinstance(r.get(f), str) and r[f].strip()):
                p.append("%s.%s: missing." % (at, f))
        if isinstance(r.get("id"), str):
            if r["id"] in ids:
                p.append(at + ".id: duplicate id.")
            ids.add(r["id"])
        start, end = r.get("start_date"), r.get("end_date")
        if not (isinstance(start, str) and DATE_RE.match(start)):
            p.append(at + '.start_date: expected "YYYY-MM".')
            start = None
        if end != "current" and not (isinstance(end, str) and DATE_RE.match(end)):
            p.append(at + '.end_date: expected "YYYY-MM" or "current".')
        elif start and end != "current" and end < start:
            p.append(at + ": end_date is before start_date.")
        if (r.get("render_policy") or {}).get("on_chart") is False:
            continue
        any_on_chart = True
        rank = (r.get("strata") or {}).get("rank")
        if not (isinstance(rank, int) and not isinstance(rank, bool) and 0 <= rank <= 12):
            p.append(at + ".strata.rank: expected an integer 0-12.")
        tags = r.get("family_tags")
        if not isinstance(tags, list) or not tags:
            p.append(at + ".family_tags: must be a non-empty array.")
            continue
        for j, t in enumerate(tags):
            if not (isinstance(t, dict) and isinstance(t.get("family_id"), str) and t["family_id"]):
                p.append("%s.family_tags[%d].family_id: missing." % (at, j))
            if not (isinstance(t, dict) and isinstance(t.get("weight"), (int, float)) and not isinstance(t.get("weight"), bool)):
                p.append("%s.family_tags[%d].weight: expected a number." % (at, j))
    if not p and not any_on_chart:
        p.append("No role is on the chart (every render_policy.on_chart is false), so there is nothing to draw.")
    return p


def embed(viewer_html, doc):
    # "<" only occurs inside JSON strings, where < is an equivalent escape. This keeps any
    # "</script>" or "<!--" in candidate text from closing the data block early.
    payload = json.dumps(doc, ensure_ascii=False, indent=1).replace("<", "\\u003c")
    if not SLOT_RE.search(viewer_html):
        raise SystemExit("viewer is missing the profile-data slot; was career-profile.html edited?")
    out = SLOT_RE.sub(lambda m: m.group(1) + "\n" + payload + "\n" + m.group(3), viewer_html, count=1)
    title = "%s, Career Ladder" % doc["candidate"]["name"].strip()
    return TITLE_RE.sub(lambda m: "<title>%s</title>" % html.escape(title), out, count=1)


def default_output(src, doc):
    name = re.sub(r"[^A-Za-z0-9]+", "", doc["candidate"]["name"].title()) or src.stem
    return src.with_name("%s_career-ladder.html" % name)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("json", type=Path, help="structured career JSON (schema 1.0)")
    ap.add_argument("-o", "--output", type=Path, help="output .html (default: <Name>_career-ladder.html beside the JSON)")
    ap.add_argument("--viewer", type=Path, default=VIEWER, help="viewer template (default: viewer/career-profile.html)")
    ap.add_argument("--skip-validate", action="store_true", help="build even if the full validator reports errors")
    args = ap.parse_args()

    try:
        doc = json.loads(args.json.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print("error: cannot read %s: %s" % (args.json, e), file=sys.stderr)
        return 1

    if not args.skip_validate:
        rep = validate(doc, str(REF_DIR))
        for f in rep.errors + rep.warns:
            print("%-5s %s\n      %s" % (f["severity"], f["path"], f["message"]), file=sys.stderr)
        if rep.errors:
            print("error: %d validator error(s); fix the JSON (or pass --skip-validate if the user accepted them)."
                  % len(rep.errors), file=sys.stderr)
            return 1

    problems = contract_problems(doc)
    if problems:
        print("error: %s does not match the viewer contract:" % args.json, file=sys.stderr)
        for line in problems:
            print("  - " + line, file=sys.stderr)
        return 1

    out_path = args.output or default_output(args.json, doc)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(embed(args.viewer.read_text(encoding="utf-8"), doc), encoding="utf-8")

    on_chart = [r for r in doc["roles"] if (r.get("render_policy") or {}).get("on_chart") is not False]
    employers = len({r["company"] for r in on_chart})
    print("Built %s" % out_path)
    print("Header will read: %d roles, %d employers (on-chart); %d role(s) in text only."
          % (len(on_chart), employers, len(doc["roles"]) - len(on_chart)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
