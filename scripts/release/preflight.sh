#!/usr/bin/env bash
#
# Release preflight checks.
# Validates package metadata, version consistency, and changelog before publishing.
#
# Checks:
#   1. npm package name is unscoped 'taskpilot'
#   2. package.json version matches pyproject.toml version
#   3. CHANGELOG.md has an entry for the target version
#   4. npm package name is available or owned by the authenticated npm user
#      (skipped when TASKPILOT_SKIP_NPM_OWNERSHIP=1; npm publish dry-run remains the auth gate)
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

# --- 1b. Package name availability / ownership ---
if [ "${TASKPILOT_SKIP_NPM_OWNERSHIP:-0}" = "1" ]; then
  echo "WARN: skipping npm ownership preflight; npm publish dry-run must prove authorization." >&2
else
  NPM_VIEW_ERR="$(mktemp)"
  if npm view "$PKG_NAME" name >/dev/null 2>"$NPM_VIEW_ERR"; then
    NPM_USER=$(npm whoami 2>/dev/null || echo "")
    if [ -z "$NPM_USER" ]; then
      echo "ERROR: npm package '$PKG_NAME' already exists, but npm ownership cannot be verified." >&2
      echo "Run 'npm login' and retry, or stop if the package is not owned by this project." >&2
      HAS_ERROR=1
    elif ! npm owner ls "$PKG_NAME" 2>/dev/null | awk '{print $1}' | grep -qx "$NPM_USER"; then
      echo "ERROR: npm package '$PKG_NAME' exists and is not owned by authenticated user '$NPM_USER'." >&2
      echo "Stop and resolve package ownership before publishing." >&2
      HAS_ERROR=1
    fi
  elif grep -q "E404\\|404 Not Found\\|Not found" "$NPM_VIEW_ERR"; then
    : # Package name appears available for first publish.
  else
    echo "ERROR: could not confirm npm package availability for '$PKG_NAME'." >&2
    cat "$NPM_VIEW_ERR" >&2
    HAS_ERROR=1
  fi
  rm -f "$NPM_VIEW_ERR"
fi

# --- 2. Version consistency ---
PY_VERSION=$(
  uv run python3 -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    print(tomllib.load(f)['project']['version'])
" 2>/dev/null
)

if [ -z "$PY_VERSION" ]; then
  # Fallback: try system python3
  PY_VERSION=$(
    python3 -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    print(tomllib.load(f)['project']['version'])
" 2>/dev/null || echo ""
  )
  # Second fallback: try python
  if [ -z "$PY_VERSION" ]; then
    PY_VERSION=$(
      python -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    print(tomllib.load(f)['project']['version'])
" 2>/dev/null || echo ""
    )
  fi
fi

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
