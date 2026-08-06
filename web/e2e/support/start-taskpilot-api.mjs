import { spawn, spawnSync } from "node:child_process";
import { cpSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, resolve, join } from "node:path";
import { fileURLToPath } from "node:url";

const supportDir = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(supportDir, "../..");
const repoRoot = resolve(webRoot, "..");
const seedWorkspaceRoot = resolve(webRoot, "e2e/fixtures/taskpilot-workspace");
const workspaceRoot = resolve(repoRoot, ".playwright/e2e-workspace");
const registryHome = resolve(repoRoot, ".playwright/taskpilot-home");
const uv = process.platform === "win32" ? "uv.cmd" : "uv";
const port = process.env.TASKPILOT_E2E_API_PORT ?? "7152";
const env = { ...process.env, TASKPILOT_HOME: registryHome };

rmSync(registryHome, { recursive: true, force: true });
mkdirSync(registryHome, { recursive: true });
rmSync(workspaceRoot, { recursive: true, force: true });
mkdirSync(dirname(workspaceRoot), { recursive: true });
cpSync(seedWorkspaceRoot, workspaceRoot, { recursive: true });

// Fixture item files carry fixed committed timestamps; restamp them to the
// current run time so the WebUI's default Updated = Last 7 days filter
// (docs/specs/0008-default-updated-filter.md) doesn't hide them.
const itemsDir = join(workspaceRoot, ".taskpilot", "items");
// Canonical UTC ISO 8601, no fractional seconds (src/taskpilot/core/models.py _check_timestamp).
const nowIso = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
const eligibleIso = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString().replace(/\.\d{3}Z$/, "Z");
for (const directory of [itemsDir, join(workspaceRoot, ".taskpilot", "archived")]) {
  if (!readdirSync(directory, { withFileTypes: true })) continue;
  for (const file of readdirSync(directory)) {
  if (!file.endsWith(".yaml")) continue;
  const path = join(directory, file);
  const restamped = readFileSync(path, "utf8")
    .replace(/^created_at: '.*'$/m, `created_at: '${file === "TP-110.yaml" ? eligibleIso : nowIso}'`)
    .replace(/^updated_at: '.*'$/m, `updated_at: '${file === "TP-110.yaml" ? eligibleIso : nowIso}'`);
  writeFileSync(path, restamped);
  }
}

const init = spawnSync(
  uv,
  ["run", "taskpilot", "init", workspaceRoot],
  { cwd: repoRoot, env, stdio: "inherit" },
);

if (init.status !== 0) {
  process.exit(init.status ?? 1);
}

const threshold = spawnSync(uv, ["run", "taskpilot", "project", "archive-threshold", "--threshold", "1"], {
  cwd: workspaceRoot,
  env,
  stdio: "inherit",
});
if (threshold.status !== 0) process.exit(threshold.status ?? 1);
const archive = spawnSync(uv, ["run", "taskpilot", "archive", "run"], {
  cwd: workspaceRoot,
  env,
  stdio: "inherit",
});
if (archive.status !== 0) process.exit(archive.status ?? 1);

const server = spawn(
  uv,
  [
    "run",
    "taskpilot",
    "serve",
    "--workspace",
    workspaceRoot,
    "--host",
    "127.0.0.1",
    "--port",
    port,
  ],
  { cwd: repoRoot, env, stdio: "inherit" },
);

server.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => {
    server.kill(signal);
  });
}
