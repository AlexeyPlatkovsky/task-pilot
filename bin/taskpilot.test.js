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
const path = require("path");
const { describe, it } = require("node:test");
const assert = require("node:assert");

const WRAPPER = path.resolve(__dirname, "taskpilot");

function run(args, env, opts) {
  return new Promise((resolve) => {
    const child = spawn("node", [WRAPPER, ...args], {
      stdio: ["ignore", "pipe", "pipe"],
      env: { ...process.env, ...env },
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
try {
  const override = process.env.TASKPILOT_PYTHON;
  if (override) {
    execSync(`"${override}" -c "import sys; print(sys.version_info[:2])"`, {
      encoding: "utf8", stdio: ["ignore", "pipe", "pipe"],
    });
    testPython = override;
  } else {
    for (const cmd of ["python3", "python"]) {
      try {
        const ver = execSync(
          `"${cmd}" -c "import sys; print(sys.version_info[:2])"`,
          { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }
        ).trim();
        const match = ver.match(/\((\d+),\s*(\d+)\)/);
        if (match && (parseInt(match[1]) > 3 || (parseInt(match[1]) === 3 && parseInt(match[2]) >= 11))) {
          testPython = cmd;
          break;
        }
      } catch { /* not found */ }
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
