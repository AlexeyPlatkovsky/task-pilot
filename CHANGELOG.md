# Changelog

All notable changes to TaskPilot are documented in this file.


## [1.1.0] - 2026-07-05

### Added

- Fix README.
- Add bump.sh script

## [1.0.0] - 2026-07-04

### Added
- Initial TaskPilot development snapshot.
- File-based task storage with Markdown/YAML canonical format.
- CLI interface (`init`, `validate`, `serve`, `project`, `item`).
- REST API with FastAPI.
- WebUI workspace with project/item management, Board and List views, validation status, filters,
  and task detail modal.
- npm release automation (F009).

### Changed
- Polished the item detail modal with grouped summary, Info, Linked to, Comments, and
  validation sections.
- Added release UI readiness behavior for last opened project restore, external-update refresh,
  hidden Tree navigation, and validation success contrast.
