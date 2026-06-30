#!/usr/bin/env node

/**
 * Integration tests for the TaskPilot npm wrapper (bin/taskpilot).
 *
 * Uses Node.js built-in test runner (node:test).
 * Run: node --test-timeout 120000 bin/taskpilot.test.js
 *
 * Requires TASKPILOT_PYTHON env var pointing to a Python >=3.11 with venv/pip,
 * or a compatible Python on PATH.
 */

const { spawn, execSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { describe, it } = require("node:test");
const assert = require("node:assert");

const WRAPPER = path.resolve(__dirname, "taskpilot");
const TEST_HOME = fs.mkdtempSync(path.join(os.tmpdir(), "taskpilot-wrapper-test-"));

function run(args, env, opts) {
  return new Promise((resolve) => {
    const child = spawn("node", [WRAPPER, ...args], {
      stdio: ["ignore", "pipe", "pipe"],
      env: {
        ...process.env,
        XDG_CACHE_HOME: path.join(TEST_HOME, "xdg-cache"),
        LOCALAPPDATA: path.join(TEST_HOME, "local-app-data"),
        ...env,
      },
      ...opts,
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d) => { stdout += d.toString(); });
    child.stderr.on("data", (d) => { stderr += d.toString(); });
    child.on("error", () => resolve({ code: 1, signal: null, stdout, stderr }));
    child.on("close", (code, signal) => {
      resolve({ code: code || 0, signal, stdout, stderr });
    });
  });
}

let testPython = null;
let testPythonExecutable = null;
function pythonIsUsable(cmd) {
  try {
    const ver = execSync(
      `"${cmd}" -c "import sys; print(sys.version_info[:2])"`,
      { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }
    ).trim();
    const match = ver.match(/\((\d+),\s*(\d+)\)/);
    if (!match || (parseInt(match[1]) === 3 && parseInt(match[2]) < 11) || parseInt(match[1]) < 3) {
      return false;
    }
    execSync(`"${cmd}" -m venv --help`, {
      encoding: "utf8", stdio: ["ignore", "pipe", "pipe"],
    });
    execSync(`"${cmd}" -m pip --version`, {
      encoding: "utf8", stdio: ["ignore", "pipe", "pipe"],
    });
    return true;
  } catch {
    return false;
  }
}

function pythonExecutable(cmd) {
  return execSync(
    `"${cmd}" -c "import sys; print(sys.executable)"`,
    { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }
  ).trim();
}

function writeFakeCommand(dir, name, content) {
  const fileName = process.platform === "win32" ? `${name}.cmd` : name;
  const filePath = path.join(dir, fileName);
  fs.writeFileSync(filePath, content);
  if (process.platform !== "win32") {
    fs.chmodSync(filePath, 0o755);
  }
  return filePath;
}

function makeFallbackPythonPath(realPython) {
  const fakeBin = fs.mkdtempSync(path.join(TEST_HOME, "fake-python-path-"));
  if (process.platform === "win32") {
    writeFakeCommand(
      fakeBin,
      "python3",
      '@echo off\r\nif "%1"=="-c" (echo 3.10.0 & exit /b 0)\r\necho old python should not be used 1>&2\r\nexit /b 1\r\n'
    );
    writeFakeCommand(fakeBin, "python", '@echo off\r\n"%TASKPILOT_TEST_REAL_PYTHON%" %*\r\nexit /b %ERRORLEVEL%\r\n');
  } else {
    writeFakeCommand(
      fakeBin,
      "python3",
      '#!/usr/bin/env bash\nif [ "$1" = "-c" ]; then echo "3.10.0"; exit 0; fi\necho "old python should not be used" >&2\nexit 1\n'
    );
    writeFakeCommand(
      fakeBin,
      "python",
      '#!/usr/bin/env node\nconst { spawnSync } = require("child_process");\nconst result = spawnSync(process.env.TASKPILOT_TEST_REAL_PYTHON, process.argv.slice(2), { stdio: "inherit" });\nprocess.exit(result.status ?? 1);\n'
    );
  }
  return fakeBin;
}

try {
  const override = process.env.TASKPILOT_PYTHON;
  if (override) {
    if (pythonIsUsable(override)) {
      testPython = override;
      testPythonExecutable = pythonExecutable(override);
    }
  } else {
    for (const cmd of ["python3", "python", "python3.14", "python3.13", "python3.12", "python3.11"]) {
      if (pythonIsUsable(cmd)) {
        testPython = cmd;
        testPythonExecutable = pythonExecutable(cmd);
        break;
      }
    }
  }
} catch { /* no Python */ }

const hasPython = !!testPython;

describe("--version", () => {
  it("prints package version and exits 0", { skip: !hasPython }, async () => {
    const { code, stdout, stderr } = await run(["--version"]);
    assert.strictEqual(code, 0, `exit code ${code}, stderr: ${stderr}`);
    assert.match(stdout, /^\d+\.\d+\.\d+\n?$/);
    assert.strictEqual(stderr, "");
  });

  it("does not trigger runtime setup", { skip: !hasPython }, async () => {
    const { code, stderr } = await run(["--version"]);
    assert.strictEqual(code, 0);
    assert.ok(!stderr.includes("setting up"), `stderr: ${stderr}`);
    assert.ok(!stderr.includes("installing"), `stderr: ${stderr}`);
  });
});

describe("Python discovery", () => {
  it("rejects non-existent TASKPILOT_PYTHON", async () => {
    const { code, stderr } = await run(["--help"], {
      TASKPILOT_PYTHON: "/nonexistent/python",
    });
    assert.strictEqual(code, 1, `stderr: ${stderr}`);
    assert.ok(stderr.includes("failed to run Python") || stderr.includes("not found"), `stderr: ${stderr}`);
  });

  it("accepts TASKPILOT_PYTHON override", { skip: !hasPython }, async () => {
    const { stderr } = await run(["--help"], {
      TASKPILOT_PYTHON: testPython,
    });
    assert.ok(
      stderr.includes("using cached runtime") || stderr.includes("setting up") || stderr.includes("using Python"),
      `stderr: ${stderr}`
    );
    assert.ok(!stderr.includes("Could not find a Python interpreter"));
  });

  it("skips incompatible python3 and falls back to compatible python", { skip: !hasPython }, async () => {
    const fakeBin = makeFallbackPythonPath(testPythonExecutable);
    const { code, stdout, stderr } = await run(["--help"], {
      PATH: `${fakeBin}${path.delimiter}${process.env.PATH}`,
      TASKPILOT_PYTHON: "",
      TASKPILOT_TEST_REAL_PYTHON: testPythonExecutable,
    });
    assert.strictEqual(code, 0, `stderr: ${stderr}`);
    assert.ok(stdout.includes("TaskPilot — local-first"), `stdout: ${stdout}`);
    assert.ok(!stderr.includes("old python should not be used"), `stderr: ${stderr}`);
  });
});

describe("doctor --rebuild-runtime", { skip: !hasPython }, () => {
  it("rebuilds the runtime and exits 0", async () => {
    const env = testPython ? { TASKPILOT_PYTHON: testPython } : {};
    const { code, stderr } = await run(["doctor", "--rebuild-runtime"], env);
    assert.strictEqual(code, 0, `stderr: ${stderr}`);
    assert.ok(stderr.includes("rebuilt successfully"), `stderr: ${stderr}`);
  });

  it("does not delegate to Python", async () => {
    const env = testPython ? { TASKPILOT_PYTHON: testPython } : {};
    const { code, stderr } = await run(["doctor", "--rebuild-runtime"], env);
    assert.strictEqual(code, 0);
    assert.ok(!stderr.includes("TaskPilot — local-first"), `stderr: ${stderr}`);
  });
});

describe("command delegation", { skip: !hasPython }, () => {
  it("forwards --help to the Python CLI", async () => {
    const env = testPython ? { TASKPILOT_PYTHON: testPython } : {};
    const { code, stdout } = await run(["--help"], env);
    assert.strictEqual(code, 0);
    assert.ok(stdout.includes("TaskPilot — local-first"), `stdout: ${stdout}`);
    assert.ok(stdout.includes("Commands"));
  });

  it("delegates init --help to the Python CLI", async () => {
    const env = testPython ? { TASKPILOT_PYTHON: testPython } : {};
    const { code, stdout } = await run(["init", "--help"], env);
    assert.strictEqual(code, 0);
    assert.ok(stdout.includes("Initialize a TaskPilot workspace"), `stdout: ${stdout}`);
  });
});
