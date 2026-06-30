#!/usr/bin/env bash
#
# Release preflight checks.
# Validates package metadata, version consistency, and changelog before publishing.
#
# Checks:
#   1. npm package name is unscoped 'taskpilot'
#   2. package.json version matches pyproject.toml version
#   3. CHANGELOG.md has an entry for the target version
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

HAS_ERROR=0

# --- 1. Package name ---
PKG_NAME=$(node -e "console.log(require('./package.json').name)" 2>/dev/null || echo "")
PKG_VERSION=$(node -e "console.log(require('./package.json').version)" 2>/dev/null || echo "")

if [ "$PKG_NAME" != "taskpilot" ]; then
  echo "ERROR: package.json name must be unscoped 'taskpilot' (got: '${PKG_NAME}')" >&2
  echo "The first release requires the unscoped npm package 'taskpilot'. Stop and" >&2
  echo "resolve the naming conflict before publishing." >&2
  HAS_ERROR=1
fi

# --- 2. Version consistency ---
PY_VERSION=$(python3 -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    print(tomllib.load(f)['project']['version'])
" 2>/dev/null || echo "")

if [ -z "$PY_VERSION" ]; then
  echo "ERROR: could not read version from pyproject.toml" >&2
  HAS_ERROR=1
elif [ "$PKG_VERSION" != "$PY_VERSION" ]; then
  echo "ERROR: package.json version ($PKG_VERSION) does not match pyproject.toml version ($PY_VERSION)" >&2
  echo "Update both files to the same version before publishing." >&2
  HAS_ERROR=1
fi

# --- 3. CHANGELOG entry ---
TARGET_VERSION="$PKG_VERSION"
if [ ! -f "CHANGELOG.md" ]; then
  echo "ERROR: CHANGELOG.md not found" >&2
  echo "Create a CHANGELOG.md with an entry for version $TARGET_VERSION before publishing." >&2
  HAS_ERROR=1
elif ! grep -q "^## \[$TARGET_VERSION\]" CHANGELOG.md 2>/dev/null; then
  echo "ERROR: CHANGELOG.md does not contain an entry for version $TARGET_VERSION" >&2
  echo "Add a '## [$TARGET_VERSION]' section to CHANGELOG.md before publishing." >&2
  HAS_ERROR=1
fi

if [ "$HAS_ERROR" -ne 0 ]; then
  echo "" >&2
  echo "Preflight FAILED. Fix the errors above and re-run." >&2
  exit 1
fi

echo "OK: preflight passed for taskpilot@${PKG_VERSION}"
