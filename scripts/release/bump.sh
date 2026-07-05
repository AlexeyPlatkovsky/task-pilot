#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <patch|minor|major> <message> [<message> ...]"
  exit 1
fi

VERSION_TYPE="$1"
shift
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

BULLETS=""
for msg in "$@"; do
  BULLETS="$BULLETS\n- $msg"
done

node -e '
var fs = require("fs");
var pkg = JSON.parse(fs.readFileSync("'"${ROOT}"'/package.json", "utf-8"));
var parts = pkg.version.split(".").map(Number);

var newVer;
if ("'"${VERSION_TYPE}"'" === "major") newVer = [parts[0] + 1, 0, 0].join(".");
else if ("'"${VERSION_TYPE}"'" === "minor") newVer = [parts[0], parts[1] + 1, 0].join(".");
else if ("'"${VERSION_TYPE}"'" === "patch") newVer = [parts[0], parts[1], parts[2] + 1].join(".");
else { console.error("Invalid version type: '"${VERSION_TYPE}"'"); process.exit(1); }

var oldVer = pkg.version;
console.log(oldVer + " -> " + newVer);

// package.json
pkg.version = newVer;
fs.writeFileSync("'"${ROOT}"'/package.json", JSON.stringify(pkg, null, 2) + "\n");

// pyproject.toml
var py = fs.readFileSync("'"${ROOT}"'/pyproject.toml", "utf-8");
py = py.replace(/^version = ".+"/m, "version = \"" + newVer + "\"");
fs.writeFileSync("'"${ROOT}"'/pyproject.toml", py);

// uv.lock
var uv = fs.readFileSync("'"${ROOT}"'/uv.lock", "utf-8");
var uvLines = uv.split("\n");
for (var i = 0; i < uvLines.length; i++) {
  if (uvLines[i] === "name = \"taskpilot\"") {
    uvLines[i + 1] = "version = \"" + newVer + "\"";
    break;
  }
}
fs.writeFileSync("'"${ROOT}"'/uv.lock", uvLines.join("\n"));

// CHANGELOG.md
var log = fs.readFileSync("'"${ROOT}"'/CHANGELOG.md", "utf-8");
var date = new Date().toISOString().slice(0, 10);
var entry = "## [" + newVer + "] - " + date + "\n\n### Added\n" + "'"${BULLETS}"'" + "\n";
var logLines = log.split("\n");
var idx = logLines.findIndex(function(l, i) { return l.startsWith("## [") && i > 2; });
logLines.splice(idx === -1 ? logLines.length : idx, 0, "", entry);
fs.writeFileSync("'"${ROOT}"'/CHANGELOG.md", logLines.join("\n"));
'
