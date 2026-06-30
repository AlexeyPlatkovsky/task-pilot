#!/usr/bin/env bash
#
# Build a clean npm package staging directory.
#
# 1. Build WebUI production assets (web/dist/).
# 2. Create a clean staging/ directory.
# 3. Copy npm package files: bin/, src/, requirements.lock, LICENSE, README.md, package.json.
# 4. Copy built WebUI assets into staging/web-dist/.
#
# The staging directory is reproducible: deleting it and re-running produces
# an identical result without dirtying source trees.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STAGING="$PROJECT_ROOT/staging"
WEB_DIR="$PROJECT_ROOT/web"
WEB_DIST="$WEB_DIR/dist"

# --- ensure clean staging directory ---
rm -rf "$STAGING"
mkdir -p "$STAGING/web-dist"

# --- build WebUI production assets ---
if [ ! -d "$WEB_DIST" ] || [ ! -f "$WEB_DIST/index.html" ]; then
  echo "Building WebUI production assets..." >&2
  (cd "$WEB_DIR" && npm run build) >&2
fi

if [ ! -d "$WEB_DIST" ] || [ ! -f "$WEB_DIST/index.html" ]; then
  echo "ERROR: WebUI build did not produce dist/index.html" >&2
  exit 1
fi

# --- copy WebUI assets ---
echo "Copying WebUI assets..." >&2
cp -R "$WEB_DIST"/* "$STAGING/web-dist/"

# --- copy Python source ---
echo "Copying Python source..." >&2
mkdir -p "$STAGING/src"
cp -R "$PROJECT_ROOT/src/taskpilot" "$STAGING/src/"

# --- copy npm package files ---
echo "Copying package files..." >&2
mkdir -p "$STAGING/bin"
cp "$PROJECT_ROOT/bin/taskpilot" "$STAGING/bin/taskpilot"
chmod +x "$STAGING/bin/taskpilot"
cp "$PROJECT_ROOT/requirements.lock" "$STAGING/requirements.lock"
cp "$PROJECT_ROOT/package.json" "$STAGING/package.json"

if [ -f "$PROJECT_ROOT/LICENSE" ]; then
  cp "$PROJECT_ROOT/LICENSE" "$STAGING/LICENSE"
fi
if [ -f "$PROJECT_ROOT/README.md" ]; then
  cp "$PROJECT_ROOT/README.md" "$STAGING/README.md"
fi

echo "Staging directory ready: $STAGING" >&2
echo "STAGING=$STAGING"
