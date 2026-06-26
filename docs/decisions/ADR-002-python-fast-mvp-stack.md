# ADR-002: Python Fast MVP Stack

- **Status:** ✅ accepted
- **Date:** 2026-06-23
- **Deciders:** TaskPilot project

## Context

TaskPilot needs a backend stack for the core domain layer, CLI, and REST API. The original
concept document suggested Node.js with TypeScript, but final stack evaluation considered
implementation speed, ecosystem maturity for file/YAML operations, and CLI ergonomics.

The WebUI remains TypeScript/React/Vite regardless of backend choice, since React + TypeScript
is the established frontend direction.

## Decision

Use Python for the core, CLI, and API server. The stack is:

- Python with `uv` for project management;
- Pydantic for models and validation;
- PyYAML for YAML read/write;
- Typer for CLI;
- FastAPI for REST API;
- pytest for tests.

The WebUI uses React, Vite, TypeScript, npm, and CSS Modules.

Business rules live in the Python core. The CLI calls the core directly. FastAPI calls the core
directly. The WebUI calls FastAPI and does not reimplement canonical validation or write rules.

## Consequences

- Single language across core, CLI, and API simplifies the backend toolchain.
- Pydantic provides strong runtime validation matching TaskPilot's validation requirements.
- Typer generates CLI help and supports JSON output with minimal boilerplate.
- FastAPI provides automatic OpenAPI docs for the REST API.
- The frontend remains TypeScript with its own build toolchain (Vite).
- Cross-language integration is limited to the REST API boundary, which is well-defined.
- Team members must be comfortable with Python.

## Alternatives Considered

- **Node.js/TypeScript monorepo** — would unify the language across frontend and backend, but
  CLI frameworks (commander, yargs) require more manual JSON output work, and YAML/file
  operations have a less mature ecosystem than Python's.
- **Rust** — too heavy for an MVP; iteration speed would suffer.
- **Go** — good CLI ergonomics but less established in the Python/data ecosystem for YAML
  manipulation.
