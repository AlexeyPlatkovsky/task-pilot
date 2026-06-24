"""Unit tests for the CLI scaffold (task F003-T1, requirement F003-R8).

Covers the foundation every command builds on: deterministic JSON output, the
human renderers, the global ``--json`` flag carried through Typer's context, and
the service-error -> exit-code translation.
"""

import typer
from typer.testing import CliRunner

from taskpilot.cli import errors, output
from taskpilot.cli.app import app, main
from taskpilot.cli.context import CLIState, get_state
from taskpilot.services.errors import (
    ConflictError,
    NotFound,
    ServiceError,
    ValidationFailed,
)

runner = CliRunner()


# --- JSON output (F003-R8) ---------------------------------------------------


def test_dumps_json_preserves_insertion_order_not_alphabetical():
    data = {"name": "VoicePilot", "key": "VP"}
    rendered = output.dumps_json(data)
    # Declared order is preserved; we must not sort_keys (key would precede name).
    assert rendered.index('"name"') < rendered.index('"key"')


def test_dumps_json_is_byte_identical_across_calls():
    data = {"id": "VP-1", "title": "Benchmark task", "tags": ["a", "b"]}
    assert output.dumps_json(data) == output.dumps_json(data)


def test_dumps_json_keeps_non_ascii_verbatim():
    assert "é" in output.dumps_json({"title": "café"})


# --- human renderers ---------------------------------------------------------


def test_render_table_includes_header_rule_and_rows():
    table = output.render_table(["ID", "TITLE"], [["VP-1", "Task one"]])
    lines = table.splitlines()
    assert lines[0].startswith("ID")
    assert set(lines[1]) <= {"-", " "}
    assert "VP-1" in lines[2]


def test_render_table_with_no_rows_still_shows_columns():
    table = output.render_table(["ID", "TITLE"], [])
    assert table.splitlines()[0].startswith("ID")


def test_render_key_values_aligns_keys():
    block = output.render_key_values([("id", "VP-1"), ("title", "Task")])
    assert "id" in block and "VP-1" in block


# --- global --json flag through Typer context --------------------------------


def _probe_app() -> typer.Typer:
    probe = typer.Typer()
    probe.callback()(main)

    @probe.command()
    def show(ctx: typer.Context):
        typer.echo("json" if get_state(ctx).json else "human")

    return probe


def test_json_flag_propagates_to_subcommand():
    result = runner.invoke(_probe_app(), ["--json", "show"])
    assert result.exit_code == 0
    assert "json" in result.output


def test_default_mode_is_human():
    result = runner.invoke(_probe_app(), ["show"])
    assert result.exit_code == 0
    assert "human" in result.output


def test_get_state_defaults_when_callback_skipped():
    ctx = typer.Context(typer.main.get_command(app))
    ctx.obj = None
    assert get_state(ctx) == CLIState(json=False)


# --- service-error -> exit-code translation (F003 exit-code constraints) -----


def _error_app() -> typer.Typer:
    err_app = typer.Typer()

    @err_app.command()
    def boom(kind: str):
        with errors.service_errors():
            if kind == "validation":
                raise ValidationFailed("title is required")
            if kind == "notfound":
                raise NotFound("no such item")
            if kind == "conflict":
                raise ConflictError("already exists")
            raise ServiceError("internal boom")

    return err_app


def test_user_errors_exit_1_with_message():
    for kind in ("validation", "notfound", "conflict"):
        # A single-command Typer app exposes the command directly (no name).
        result = runner.invoke(_error_app(), [kind])
        assert result.exit_code == 1, kind
        assert "Error:" in result.output


def test_unexpected_service_error_exits_2():
    result = runner.invoke(_error_app(), ["other"])
    assert result.exit_code == 2


def test_root_help_lists_json_flag():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--json" in result.output
