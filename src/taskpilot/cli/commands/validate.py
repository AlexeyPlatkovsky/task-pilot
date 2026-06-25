"""``taskpilot validate`` — workspace validation (task F003-T7, requirement F003-R7).

Runs the F001 validator over the current workspace and reports findings. Exit
code follows the report: ``0`` when there are no error-severity findings,
``1`` otherwise (warnings alone do not fail). Output channels follow the CLI
contract: human findings go to stderr (so a clean run leaves stderr empty,
scenario F003-S7); the structured ``--json`` report goes to stdout.
"""

from __future__ import annotations

import typer

from taskpilot.cli.context import get_state
from taskpilot.cli.errors import service_errors
from taskpilot.cli.exit_codes import EXIT_OK, EXIT_SYSTEM_ERROR, EXIT_USER_ERROR
from taskpilot.cli.output import print_json, print_line
from taskpilot.cli.workspace import find_workspace
from taskpilot.core.validation import Finding, ValidationReport, validate_workspace

__all__ = ["register"]


def _format_finding(finding: Finding) -> str:
    """Render a finding as ``<severity>: <path>[:<field>]: <message>``."""
    location = finding.path
    if finding.field:
        location = f"{location}:{finding.field}"
    return f"{finding.severity.value}: {location}: {finding.message}"


def validate_command(ctx: typer.Context) -> None:
    """Validate the current workspace and exit non-zero when errors are found."""
    state = get_state(ctx)
    with service_errors():
        paths = find_workspace()
        try:
            report: ValidationReport = validate_workspace(paths)
        except OSError as exc:
            typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(EXIT_SYSTEM_ERROR) from exc

    if state.json:
        print_json(report.to_dict())
    else:
        for finding in report.findings:
            typer.echo(_format_finding(finding), err=True)
        if report.ok:
            print_line("Workspace is valid.")
        else:
            typer.echo(
                f"Found {report.error_count} error(s), {report.warning_count} warning(s).",
                err=True,
            )

    raise typer.Exit(EXIT_OK if report.ok else EXIT_USER_ERROR)


def register(app: typer.Typer) -> None:
    """Attach the ``validate`` command to ``app``."""
    app.command("validate")(validate_command)
