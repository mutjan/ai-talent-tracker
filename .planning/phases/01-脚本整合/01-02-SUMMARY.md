---
phase: 01-脚本整合
plan: 02
subsystem: config
tags: [json-config, python, tavily, search]

# Dependency graph
requires:
  - phase: none
    provides: nothing (standalone config module)
provides:
  - scripts/search_config.json (externalized query and domain configuration)
  - scripts/config_loader.py (config loading, validation, and defaults merging)
  - tests/test_search.py (24 tests for CONS-02 and CONS-03)
affects: [01-01-合并脚本, 03-扩展覆盖, 04-动态查询]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "External JSON config with Python loader module"
    - "Recursive defaults merging with user overrides"
    - "Named query groups and domain groups with enable flags"

key-files:
  created:
    - scripts/search_config.json
    - scripts/config_loader.py
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_search.py
  modified: []

key-decisions:
  - "JSON file for config (not YAML) -- zero new dependencies, consistent with project's JSON-only data"
  - "Separate config_loader.py module -- keeps loader logic testable independently from search script"
  - "Recursive defaults merging -- allows partial configs while guaranteeing structure"

patterns-established:
  - "Config externalization: queries and domains defined in search_config.json, loaded via config_loader.py"
  - "Named groups: query groups (english_broad, english_specific, chinese_broad, chinese_specific) and domain groups (english_tech, chinese_tech, social) with per-group enable flags"
  - "Validation contract: _validate_config() checks structure before use, raises ValueError with descriptive messages"

requirements-completed: [CONS-02, CONS-03]

# Metrics
duration: 7min
completed: 2026-04-08
---

# Phase 1 Plan 02: 外部化搜索配置 Summary

**JSON config file with named query/domain groups and Python loader with validation -- zero new dependencies**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-08T08:37:20Z
- **Completed:** 2026-04-08T08:45:12Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Externalized search queries from hardcoded lists to `scripts/search_config.json` with 4 named query groups
- Abstracted domain sets into 3 named groups (english_tech/chinese_tech/social) with per-group enable flags
- Built config_loader.py with load, validate, merge defaults, and filter functions
- 24 passing tests covering config structure, validation, defaults merging, and domain filtering

## Task Commits

Each task was committed atomically:

1. **Task 1: External config file and loader module** - `c69d256` (feat)
2. **Task 2: Config structure and domain group tests** - `9f146ae` (test)

## Files Created/Modified
- `scripts/search_config.json` - External JSON config with query groups and domain groups
- `scripts/config_loader.py` - Config loading, validation, defaults merging, domain/query filtering
- `tests/__init__.py` - Package marker
- `tests/conftest.py` - Shared fixtures (config_path, sample_events, mock_tavily_response, tmp_config)
- `tests/test_search.py` - 24 tests for CONS-02 and CONS-03

## Decisions Made
- **JSON over YAML for config**: Project uses JSON everywhere (events.json, candidates). No reason to add a YAML dependency.
- **Separate config_loader.py module**: Keeps the loader testable and importable independently. The merged search script (from 01-01) will import from it.
- **Recursive defaults merging**: Users can provide partial configs (e.g., just override max_results) without specifying the full structure.
- **Validation runs after merge**: The merge guarantees top-level keys exist, so validation focuses on sub-structure (required groups, non-empty queries).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Config file and loader ready for the merged search script (01-01) to import
- Domain groups with enable/disable flags ready for Phase 3 (add chinese_tech domains, enable social group)
- Query groups with empty chinese placeholders ready for Phase 3 (add Chinese queries)
- Tests provide regression safety for config structure changes

---
*Phase: 01-脚本整合*
*Completed: 2026-04-08*
