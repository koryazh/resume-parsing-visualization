#!/usr/bin/env bash
# Package the skill as an installable zip.
# Output: dist/resume-parsing-visualization-skill-YYYY-MM-DD-HHMM.zip
set -euo pipefail

SKILL="resume-parsing-visualization"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP="$(date +%Y-%m-%d-%H%M)"
OUT="$ROOT/dist/${SKILL}-skill-${STAMP}.zip"

# Constant-named copy for GitHub Release assets. A release asset name must
# not change between versions, otherwise the permanent
# releases/latest/download/<name> URL breaks. The stamped file above stays
# as the local build record.
RELEASE_OUT="$ROOT/dist/${SKILL}-skill.zip"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$STAGE/$SKILL" "$ROOT/dist"

# Only the files the skill itself needs, plus LICENSE, which must travel
# with the zip because the zip is what users download. README, .gitignore,
# and this script are repo scaffolding and are deliberately left out.
for item in SKILL.md LICENSE reference reference-data docs scripts; do
  cp -R "$ROOT/$item" "$STAGE/$SKILL/"
done

find "$STAGE" -name '.DS_Store' -delete
find "$STAGE" -name '__pycache__' -type d -prune -exec rm -rf {} +

( cd "$STAGE" && zip -qr "$OUT" "$SKILL" -x '*.DS_Store' '*__pycache__*' )

cp "$OUT" "$RELEASE_OUT"

echo "Packaged: $OUT"
echo "Release asset: $RELEASE_OUT"
unzip -Z1 "$OUT" | sed 's/^/  /'
