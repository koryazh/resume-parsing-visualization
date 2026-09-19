#!/usr/bin/env python3
"""
Self-test for the bundled viewer: the constants it hardcodes must match this skill's own files.

    python3 scripts/check_viewer.py

The viewer (viewer/career-profile.html) draws the ladder in the browser, so it carries its own copy of
the 13 levels and the sphere palette. Those copies are the one place this skill can silently disagree
with itself: edit a level name in reference-data/leveling-framework.json, and every chart keeps printing
the old one. This script fails if that happens.

Checks:
  - LEVELS block (rank, code, name) == reference-data/leveling-framework.json
  - SPHERE_COLORS + SPHERE_COLOR_BEYOND == the palette table in docs/visualization-technical-spec.md
  - the spec version stamped in the viewer's <meta name="generator"> == the spec's "Spec version" line
  - the profile-data slot and the Save as PDF handler are still present

Exit 0 = consistent, 1 = drift. Run it after touching the framework, the palette, or the viewer, and
before packaging. Standard library only.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEWER = ROOT / "viewer" / "career-profile.html"
FRAMEWORK = ROOT / "reference-data" / "leveling-framework.json"
SPEC = ROOT / "docs" / "visualization-technical-spec.md"


def block(text, name):
    m = re.search(r"/\* %s:BEGIN.*?\*/(.*?)/\* %s:END \*/" % (name, name), text, re.S)
    if not m:
        raise SystemExit("viewer is missing the %s:BEGIN/END markers" % name)
    return m.group(1)


def main():
    viewer = VIEWER.read_text(encoding="utf-8")
    spec = SPEC.read_text(encoding="utf-8")
    framework = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    problems = []

    expected = [(l["rank"], l["code"], l["name"]) for l in sorted(framework["levels"], key=lambda l: l["rank"])]
    found = [(int(r), c, n) for r, c, n in
             re.findall(r'rank:\s*(\d+),\s*code:\s*"([^"]+)",\s*name:\s*"([^"]+)"', block(viewer, "LEVELS"))]
    if found != expected:
        problems.append("LEVELS differ from leveling-framework.json v%s:\n    viewer:    %s\n    framework: %s"
                        % (framework.get("version"), found, expected))

    table = re.search(r"### 5\.8 Sphere color palette(.*?)###", spec, re.S)
    spec_hexes = [h.lower() for h in re.findall(r"`(#[0-9a-fA-F]{6})`", table.group(1))] if table else []
    viewer_hexes = [h.lower() for h in re.findall(r'"(#[0-9a-fA-F]{6})"', block(viewer, "PALETTE"))]
    if viewer_hexes != spec_hexes:
        problems.append("Palette differs from spec 5.8:\n    viewer: %s\n    spec:   %s" % (viewer_hexes, spec_hexes))

    spec_ver = re.search(r"^- Spec version:\s*([\d.]+)", spec, re.M)
    viewer_ver = re.search(r"visualization spec ([\d.]+)", viewer)
    if not viewer_ver:
        problems.append("viewer <meta name=generator> does not name a visualization spec version")
    elif spec_ver and spec_ver.group(1) != viewer_ver.group(1):
        problems.append("viewer targets visualization spec %s but docs/visualization-technical-spec.md is %s"
                        % (viewer_ver.group(1), spec_ver.group(1)))

    if '<script type="application/json" id="profile-data">' not in viewer:
        problems.append("viewer has no profile-data slot; scripts/build_profile.py cannot bake a JSON into it")
    if "window.print" not in viewer:
        problems.append("viewer has no window.print handler; the Save as PDF control was dropped (spec 4.11)")

    if problems:
        print("DRIFT:")
        for p in problems:
            print("  - " + p)
        return 1
    print("viewer consistent: %d levels, %d palette colours, spec %s"
          % (len(found), len(viewer_hexes), viewer_ver.group(1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
