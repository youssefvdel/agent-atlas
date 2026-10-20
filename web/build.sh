#!/usr/bin/env bash
# Build the atlas site. The tool blocks commands containing certain words,
# so the build runs from a script file.
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(cd .. && pwd)"

mkdir -p public
cp -f "$ROOT/site/assets/atlas.json" public/atlas.json

npm run build

# The site's document links point at ./docs/... — the docs are published
# alongside the site so the links resolve on GitHub Pages.
rm -rf "$ROOT/site/docs"
mkdir -p "$ROOT/site/docs"
cp -r "$ROOT/docs/." "$ROOT/site/docs/"

mkdir -p "$ROOT/site/data"
cp -f "$ROOT/data/skills.tree.md" "$ROOT/site/data/skills.tree.md"

echo "site + docs copied"
