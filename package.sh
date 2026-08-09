#!/usr/bin/env bash
# Package the skill as an installable zip.
# Output: dist/resume-parsing-visualization-skill-YYYY-MM-DD-HHMM.zip
set -euo pipefail

SKILL="resume-parsing-visualization"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP="$(date +%Y-%m-%d-%H%M)"
OUT="$ROOT/dist/${SKILL}-skill-${STAMP}.zip"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$STAGE/$SKILL" "$ROOT/dist"

# Only the files the skill itself needs. README, .gitignore, and this
# script are repo scaffolding and are deliberately left out of the zip.
for item in SKILL.md reference reference-data docs scripts; do
  cp -R "$ROOT/$item" "$STAGE/$SKILL/"
done

find "$STAGE" -name '.DS_Store' -delete
find "$STAGE" -name '__pycache__' -type d -prune -exec rm -rf {} +

( cd "$STAGE" && zip -qr "$OUT" "$SKILL" -x '*.DS_Store' '*__pycache__*' )

echo "Packaged: $OUT"
unzip -Z1 "$OUT" | sed 's/^/  /'
