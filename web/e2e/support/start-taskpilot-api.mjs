import { spawn, spawnSync } from "node:child_process";
import { cpSync, mkdirSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
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

const init = spawnSync(
  uv,
  ["run", "taskpilot", "init", workspaceRoot],
  { cwd: repoRoot, env, stdio: "inherit" },
);

if (init.status !== 0) {
  process.exit(init.status ?? 1);
}

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
