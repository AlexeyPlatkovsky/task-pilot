#!/usr/bin/env bash
#
# Release preflight checks.
# Fails if the npm package name is not "taskpilot" or the package is scoped.
#

set -euo pipefail

PKG_NAME=$(node -e "console.log(require('../package.json').name)" 2>/dev/null || echo "")

if [ "$PKG_NAME" != "taskpilot" ]; then
  echo "ERROR: package.json name must be unscoped 'taskpilot' (got: '${PKG_NAME}')" >&2
  echo "The first release requires the unscoped npm package 'taskpilot'. Stop and" >&2
  echo "resolve the naming conflict before publishing." >&2
  exit 1
fi

echo "OK: package name is 'taskpilot'"
