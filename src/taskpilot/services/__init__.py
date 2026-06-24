"""TaskPilot domain/service layer (feature F002).

Stateless business-rule operations for projects, items, comments, and links.
This is the single source of business rules shared by the CLI, REST API, and
future MCP adapters. Services orchestrate the F001 storage primitives in
``taskpilot.core`` and own domain rules (hierarchy, links, soft delete,
pre-write validation); they never import adapter or framework code.
"""
