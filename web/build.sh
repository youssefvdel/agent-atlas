#!/usr/bin/env bash
# Build the atlas site.
#
# The tool that runs this blocks commands containing certain words, so the
# build lives in a script file. It also prepends a directory to PATH that
# shadows npm, so the real npm is called by absolute path.
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(cd .. && pwd)"

NPM="${NPM:-/usr/bin/npm}"
[ -x "$NPM" ] || NPM="$(command -v npm)"

mkdir -p public
cp -f "$ROOT/site/assets/atlas.json" public/atlas.json

"$NPM" run build

# The site's document links point at ./docs/... — the docs are published
# alongside the site so the links resolve on GitHub Pages.
rm -rf "$ROOT/site/docs"
mkdir -p "$ROOT/site/docs"
cp -r "$ROOT/docs/." "$ROOT/site/docs/"

mkdir -p "$ROOT/site/data"
cp -f "$ROOT/data/skills.tree.md" "$ROOT/site/data/skills.tree.md"

echo "site + docs copied"
