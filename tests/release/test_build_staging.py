from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def test_build_staging_rebuilds_web_dist_when_existing_dist_is_stale(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    fake_root = tmp_path / "repo"

    (fake_root / "scripts" / "release").mkdir(parents=True)
    shutil.copy2(
        repo_root / "scripts" / "release" / "build-staging.sh",
        fake_root / "scripts" / "release" / "build-staging.sh",
    )

    (fake_root / "web" / "dist").mkdir(parents=True)
    (fake_root / "web" / "dist" / "index.html").write_text("stale\n", encoding="utf-8")
    (fake_root / "src" / "taskpilot").mkdir(parents=True)
    (fake_root / "src" / "taskpilot" / "__init__.py").write_text("", encoding="utf-8")
    (fake_root / "bin").mkdir()
    (fake_root / "bin" / "taskpilot").write_text(
        "#!/usr/bin/env bash\n", encoding="utf-8"
    )
    (fake_root / "requirements.lock").write_text("", encoding="utf-8")
    (fake_root / "package.json").write_text('{"name":"taskpilot"}\n', encoding="utf-8")

    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    npm_log = tmp_path / "npm.log"
    npm_stub = stub_bin / "npm"
    npm_stub.write_text(
        "#!/usr/bin/env bash\n"
        'printf \'%s\\n\' "$*" >> "$NPM_LOG"\n'
        "mkdir -p dist\n"
        "printf 'current\\n' > dist/index.html\n",
        encoding="utf-8",
    )
    npm_stub.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{stub_bin}{os.pathsep}{env['PATH']}"
    env["NPM_LOG"] = str(npm_log)

    result = subprocess.run(
        ["bash", "scripts/release/build-staging.sh"],
        cwd=fake_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert npm_log.read_text(encoding="utf-8") == "run build\n"
    assert (fake_root / "staging" / "web-dist" / "index.html").read_text(
        encoding="utf-8"
    ) == "current\n"
