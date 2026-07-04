#!/usr/bin/env bash
#
# Two-stage npm publish workflow.
#
# Stage 1 (--dry-run): build the staging directory and run "npm publish --dry-run".
#   Must succeed before stage 2.
#
# Stage 2 (--publish): real npm publish from the staging directory.
#   Requires explicit approval and valid npm credentials.
#
# Usage:
#   bash scripts/release/publish.sh --dry-run     # validate the package
#   bash scripts/release/publish.sh --publish     # real publish (prompts for approval)
#
# Set NPM_DIST_TAG to override the default npm dist-tag. Stable releases default to "latest".
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STAGING="$PROJECT_ROOT/staging"
NPM_DIST_TAG="${NPM_DIST_TAG:-latest}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

run_dry_run() {
  echo "=== Stage 1: npm publish --dry-run ==="
  echo ""

  # --- preflight ---
  echo "Running preflight checks..."
  bash "$SCRIPT_DIR/preflight.sh"
  echo ""

  # --- build staging ---
  echo "Building staging directory..."
  bash "$SCRIPT_DIR/build-staging.sh"
  echo ""

  # --- dry-run publish ---
  echo "Running npm publish --dry-run in staging/ with tag '$NPM_DIST_TAG'..."
  (cd "$STAGING" && npm publish --dry-run --access public --tag "$NPM_DIST_TAG" 2>&1)
  local rc=$?

  if [ "$rc" -ne 0 ]; then
    echo ""
    echo -e "${RED}Dry-run publish FAILED.${NC} Fix the errors above before attempting a real publish." >&2
    exit 1
  fi

  echo ""
  echo -e "${GREEN}Dry-run publish PASSED.${NC}"
  echo ""
  echo "The staging directory is ready at: $STAGING"
  echo ""
  echo "To proceed with real publish, review the dry-run output above and run:"
  echo "  bash scripts/release/publish.sh --publish"
}

run_publish() {
  echo "=== Stage 2: Real npm publish ==="
  echo ""

  # --- staging must exist ---
  if [ ! -f "$STAGING/package.json" ]; then
    echo -e "${RED}ERROR: staging directory not found at $STAGING${NC}" >&2
    echo "Run the dry-run first: bash scripts/release/publish.sh --dry-run" >&2
    exit 1
  fi

  # --- credentials check ---
  echo "Checking npm credentials..."
  local npm_user
  npm_user=$(npm whoami 2>/dev/null || echo "")
  if [ -z "$npm_user" ]; then
    echo -e "${RED}ERROR: not logged in to npm.${NC}" >&2
    echo "Run 'npm login' to authenticate before publishing." >&2
    exit 1
  fi
  echo "  Authenticated as: $npm_user"

  # --- check npm registry ---
  local registry
  registry=$(npm config get registry 2>/dev/null || echo "https://registry.npmjs.org/")
  echo "  Registry: $registry"

  # --- manual approval ---
  local pkg_version
  pkg_version=$(node -e "console.log(require('$STAGING/package.json').version)" 2>/dev/null || echo "")
  local pkg_name
  pkg_name=$(node -e "console.log(require('$STAGING/package.json').name)" 2>/dev/null || echo "")

  echo ""
  echo -e "${YELLOW}About to publish ${pkg_name}@${pkg_version} to ${registry} with tag '${NPM_DIST_TAG}'${NC}"
  echo -e "${YELLOW}Authenticated as: ${npm_user}${NC}"
  echo ""
  echo "This is a REAL publish. The package will be publicly available."
  echo ""
  read -r -p "Type the package name '${pkg_name}' to confirm: " confirm

  if [ "$confirm" != "$pkg_name" ]; then
    echo -e "${RED}Publish ABORTED.${NC} Confirmation did not match '${pkg_name}'." >&2
    exit 1
  fi

  echo ""
  echo "Publishing..."
  (cd "$STAGING" && npm publish --access public --tag "$NPM_DIST_TAG" 2>&1)
  local rc=$?

  if [ "$rc" -ne 0 ]; then
    echo ""
    echo -e "${RED}Publish FAILED.${NC}" >&2
    exit 1
  fi

  echo ""
  echo -e "${GREEN}Published ${pkg_name}@${pkg_version} successfully.${NC}"
}

case "${1:-}" in
  --dry-run)
    run_dry_run
    ;;
  --publish)
    run_publish
    ;;
  *)
    echo "Usage: bash scripts/release/publish.sh --dry-run | --publish" >&2
    echo "" >&2
    echo "  --dry-run   Build staging and validate the package (no publish)." >&2
    echo "  --publish   Real npm publish (requires --dry-run first, manual approval)." >&2
    exit 1
    ;;
esac
