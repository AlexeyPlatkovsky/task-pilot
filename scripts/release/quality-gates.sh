#!/usr/bin/env bash
#
# Release quality gates.
#
# Runs the full quality suite before npm publish:
#   1. Python tests (pytest)
#   2. Python lint (ruff check)
#   3. Python format (ruff format --check)
#   4. WebUI unit/component tests (vitest)
#   5. WebUI browser contract tests
#   6. WebUI functional E2E tests
#   7. WebUI production build
#   8. npm package staging build
#   9. npm publish dry-run
#
# Fails on the first check that doesn't pass.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
FAILURES=()

check_pass() {
  echo -e "  ${GREEN}OK${NC}: $1"
  PASSED=$((PASSED + 1))
}

check_fail() {
  echo -e "  ${RED}FAIL${NC}: $1"
  FAILED=$((FAILED + 1))
  FAILURES+=("$1")
}

run_check() {
  local label="$1"
  shift
  echo ""
  echo "--- $label ---"
  if "$@"; then
    check_pass "$label"
  else
    check_fail "$label"
  fi
}

# --- Python ---
run_check "Python tests" uv run pytest --tb=short -q
run_check "Python lint" uv run ruff check .
run_check "Python format" uv run ruff format --check .

# --- WebUI ---
run_check "WebUI unit/component tests" npm --prefix web run test:component
run_check "WebUI browser contract" npm --prefix web run test:browser-contract
run_check "WebUI functional E2E" npm --prefix web run test:e2e:functional
run_check "WebUI production build" npm --prefix web run build

# --- Package ---
run_check "npm package staging build" bash scripts/release/build-staging.sh

# --- npm dry-run ---
run_check "npm publish dry-run" npm publish --dry-run --prefix staging

# --- Summary ---
echo ""
echo "=========================================="
echo "Quality gates: $PASSED passed, $FAILED failed"
if [ "$FAILED" -gt 0 ]; then
  echo ""
  echo "Failures:"
  for f in "${FAILURES[@]}"; do
    echo "  - $f"
  done
  exit 1
fi
echo "All quality gates passed."
