---
phase: 03-mapping-config
plan: "02"
subsystem: config
tags:
  - config-loader
  - caching
  - validation
  - tdd
  - mongodb
  - pytest-asyncio
dependency_graph:
  requires:
    - phase: 03-mapping-config-01
      provides: ConfigCache (TTL in-memory cache), ConfigValidator (field mapping integrity checks)
    - phase: 01-foundation
      provides: MappingConfig model, MappingConfigRepository, FileType enum, FieldMapping types
  provides:
    - ConfigLoader: Orchestrates config loading from MongoDB with caching and validation
    - ConfigLoadError: Structured exception with validation_errors list
    - Config package exports: ConfigCache, ConfigValidator, ConfigLoader, ConfigLoadError, ConfigValidationError
  affects:
    - Future phases that consume MappingConfig (ExcelStreamReader, Normalizer, Dynamic Mapper)
tech_stack:
  added:
    - pytest-asyncio (async test support)
    - pydantic-settings (pre-existing dependency, installed for test suite)
  patterns:
    - TDD RED→GREEN cycle
    - Dependency injection (repository, cache, validator)
    - Cache-then-DB loading pattern
    - Structured error handling with validation_errors
key-files:
  created:
    - src/config/loader.py
    - tests/test_config_loader.py
  modified:
    - src/config/__init__.py
    - pyproject.toml
key-decisions:
  - "ConfigLoadError is a dataclass Exception (not pydantic model) for lightweight error raising"
  - "Cache key format uses FileType enum .value for type safety"
  - "Shared _validate_and_cache method reduces duplication between load_by_partner_type and load_by_version"
  - "asyncio_mode = 'auto' in pyproject.toml eliminates need for explicit @pytest.mark.asyncio decorators"
patterns-established:
  - "Cache-then-DB: check cache first, query repository on miss, validate before caching"
  - "Structured errors: ConfigLoadError carries validation_errors list for debugging"
  - "Dependency injection: ConfigLoader receives repository/cache/validator as constructor args"
requirements-completed:
  - CONFIG-01
  - CONFIG-02
metrics:
  duration_minutes: ~8
  completed_date: "2026-05-27"
  tests_created: 17
  tests_passed: 166
  files_created: 2
  lines_added: ~584
---

# Phase 03 Plan 02: ConfigLoader Summary

**ConfigLoader service integrating MappingConfigRepository, ConfigCache, and ConfigValidator to load, cache, validate, and version-resolve mapping configurations from MongoDB**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-05-27T10:15:00Z
- **Completed:** 2026-05-27T10:23:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- ConfigLoader service with cache-then-DB loading pattern
- load_by_partner_type: loads config by partner/workflow/file_type with caching
- load_by_version: loads specific config version by partner + version string
- ConfigLoadError with structured validation_errors for debugging
- Config package exports updated with all public classes
- 17 new tests (TDD-driven), 166/166 total tests pass (no regressions)

## Task Commits

Each task was committed atomically:

1. **task 1: Build ConfigLoader with repository, cache, and validator integration** - `35ed05b` (test: add failing tests), `a520d9b` (feat: implement ConfigLoader)
2. **task 2: Run full test suite and verify integration** - `21efcf8` (chore: add asyncio_mode)

**Plan metadata:** _pending final commit_

## Files Created/Modified

- `src/config/loader.py` — ConfigLoader class with ConfigLoadError, load_by_partner_type, load_by_version, invalidate_cache
- `src/config/__init__.py` — Package exports for ConfigCache, ConfigValidator, ConfigLoader, ConfigLoadError, ConfigValidationError
- `tests/test_config_loader.py` — 17 tests covering cache hit/miss, validation errors, required_paths, version loading, TTL
- `pyproject.toml` — Added asyncio_mode = "auto" to pytest config

## Decisions Made

- ConfigLoadError is a dataclass Exception (not pydantic model) — lighter weight, simpler to raise/catch
- Cache key format: `{partner}:{workflow_type}:{file_type.value}:latest` for partner_type, `{partner}:*:*:{version}` for version — uses FileType enum .value for type safety
- Shared `_validate_and_cache` method eliminates duplication between load_by_partner_type and load_by_version
- asyncio_mode = "auto" in pyproject.toml — eliminates need for explicit @pytest.mark.asyncio on every async test

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed test ConfigLoadError reference scope**
- **Found during:** task 1 (GREEN phase test run)
- **Issue:** Test methods used `ConfigLoadError` directly but it was only imported as `self.ConfigLoadError` in setup_method
- **Fix:** Changed `pytest.raises(ConfigLoadError)` to `pytest.raises(self.ConfigLoadError)` in TestLoadByPartnerType and TestLoadByVersion classes
- **Files modified:** `tests/test_config_loader.py`
- **Verification:** All 17 tests pass after fix
- **Committed in:** `a520d9b` (part of task 1 commit)

**2. [Rule 3 - Blocking] Installed missing pytest-asyncio dependency**
- **Found during:** task 1 (test execution)
- **Issue:** pytest-asyncio not installed, async tests could not run
- **Fix:** `pip install pytest-asyncio`
- **Files modified:** system packages (no project files)
- **Verification:** Async tests run successfully
- **Committed in:** N/A (system dependency)

**3. [Rule 3 - Blocking] Installed missing pydantic-settings dependency**
- **Found during:** task 2 (full test suite)
- **Issue:** pydantic-settings not installed, test_settings.py failed on import
- **Fix:** `pip install pydantic-settings`
- **Files modified:** system packages (no project files)
- **Verification:** Full test suite passes (166/166)
- **Committed in:** N/A (system dependency)

---

**Total deviations:** 3 auto-fixed (3 blocking dependency/scope issues)
**Impact on plan:** All auto-fixes necessary for test execution. No scope creep.

## Known Stubs

None — all functionality is fully implemented and wired.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: tampering | src/config/loader.py | ConfigLoader validates every config from MongoDB before caching or returning; invalid configs rejected with ConfigLoadError (mitigates T-03-06) |
| threat_flag: spoofing | src/config/loader.py | Cache keys use FileType enum .value (not raw string), partner/workflow_type validated by repository query (mitigates T-03-07) |
| threat_flag: dos | src/config/loader.py | ConfigLoadError includes validation_errors for debugging; no infinite retry; cache miss → single DB query (mitigates T-03-08) |
| threat_flag: info-disclosure | src/config/loader.py | ConfigLoadError.message is generic ("Config validation failed"); detailed errors only in validation_errors list (mitigates T-03-09) |

## Verification

- `python -m pytest tests/test_config_loader.py -x -v` — 17/17 passed ✓
- `python -m pytest tests/test_config_cache.py tests/test_config_validator.py tests/test_config_loader.py -x -v` — 53/53 passed ✓
- `python -m pytest tests/ -x -v` — 166/166 passed, no regressions ✓
- `src/config/loader.py` has ConfigLoader with load_by_partner_type and load_by_version methods ✓
- `src/config/__init__.py` exports ConfigCache, ConfigValidator, ConfigLoader, ConfigLoadError ✓
- ConfigLoadError includes validation_errors for structured error handling ✓
- Cache integration verified: cache hit skips DB, cache miss queries DB ✓

## Self-Check: PASSED
