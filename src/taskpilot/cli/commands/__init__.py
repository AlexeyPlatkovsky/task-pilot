"""Command modules for the TaskPilot CLI (feature F003).

Each module defines a command (or command group) and a ``register(app)`` hook;
:mod:`taskpilot.cli.app` calls every hook so commands attach without importing
the root app (avoiding a circular import).
"""
