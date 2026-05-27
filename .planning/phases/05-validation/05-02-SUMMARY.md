---
phase: 05-validation
plan: 02
subsystem: validation
tags: [duplicate-detection, validator, repository, tdd, async]
dependency_graph:
  requires:
    - src/validators/validator.py (Plan 01 output — Validator class)
    - src/models/data_container.py (DataContainerRepository)
    - src/models/reconciliation_file.py (ReconciliationFileRepository.find_by_file_hash)
  provides:
    - DataContainerRepository.find_by_duplicate_key method
    - Validator.validate_with_duplicates() async method
    - Validator._check_transaction_duplicate() async method
    - Validator._check_file_duplicate() async method
  affects:
    - Future: ingestion pipeline (calls validate_with_duplicates before persistence)
tech_stack:
  added:
    - async/await pattern for duplicate detection
    - TYPE_CHECKING imports for repository type hints
    - unittest.mock.AsyncMock for async repository mocking
  patterns:
    - TDD (RED-GREEN-REFACTOR)
    - graceful degradation (repos optional, checks skipped if not provided)
    - error collection (core + duplicate errors combined)
key_files:
  created: []
  modified:
    - src/models/data_container.py (find_by_duplicate_key method added)
    - src/validators/validator.py (constructor + 3 new async methods)
    - tests/test_models.py (2 new async tests for find_by_duplicate_key)
    - tests/test_validator.py (16 new tests across 3 test classes)
decisions:
  - "Validator constructor accepts optional repositories — enables testing without MongoDB"
  - "validate_with_duplicates() always runs core validation first, then duplicate checks"
  - "Duplicate errors collected alongside core errors (not fail-fast, consistent with existing pattern)"
  - "Transaction duplicate requires trace parameter — without trace, check is skipped"
  - "File duplicate error truncates hash to 16 chars in reason string for readability"
metrics:
  duration: "~10 minutes"
  completed: "2026-05-27"
  tests_added: 18
  total_tests: 42 (test_validator.py), 267 (full suite)
  test_classes_added: 3
  files_modified: 4
  lines_added: "~720"
---

# Phase 05 Plan 02: Duplicate Detection Summary

**One-liner:** Duplicate detection for transactions (identify + reconciliationDate + trace) and files (SHA256 fileHash) with async repository lookups, mocked tests, and graceful degradation when repositories are not provided.

## Tasks Completed

| task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Add DataContainerRepository.find_by_duplicate_key method | `a3ea596` | `src/models/data_container.py`, `tests/test_models.py` |
| 2 | Extend Validator with duplicate detection (transaction + file level) | `7163c5e` | `src/validators/validator.py`, `tests/test_validator.py` |
| 3 | Full integration test suite — all validation rules + duplicate detection combined | `76f8817` | `tests/test_validator.py` |

## Implementation Details

### DataContainerRepository.find_by_duplicate_key

```
DataContainerRepository
└── find_by_duplicate_key(identify, reconciliation_date, trace) → Optional[DataContainer]
    └── Query: {"identify": identify, "reconciliationDate": reconciliation_date, "partnerData.trace": trace}
```

Uses existing indexes (idx_identify_date + idx_trace) for efficient compound queries. Returns first match or None.

### Validator Duplicate Detection

```
Validator
├── __init__(data_container_repo?, reconciliation_file_repo?)
├── validate(txn, row_number?, trace?) → ValidationResult          # existing, unchanged
├── validate_with_duplicates(txn, identify, reconciliation_date, file_hash?, row_number?, trace?) → ValidationResult
│   ├── validate() — core validation (required fields, decimal, date, status)
│   ├── _check_transaction_duplicate() — identify + date + trace lookup
│   └── _check_file_duplicate() — file_hash lookup
├── _check_transaction_duplicate(identify, reconciliation_date, trace, row_number) → Optional[ValidationError]
│   └── field="duplicate", reason="transaction already exists in data_container"
└── _check_file_duplicate(file_hash) → Optional[ValidationError]
    └── field="file_duplicate", reason="file already processed (hash: {hash[:16]}...)"
```

### Error Collection Pattern

Core validation errors collected first, then duplicate errors appended. All errors share the same ValidationResult. `is_valid = False` when any error present.

## Test Coverage

| Test Class | Tests | Coverage |
|------------|-------|----------|
| TestDataContainerRepository (new) | 2 | find_by_duplicate_key no-match + match |
| TestDuplicateDetection | 7 | Transaction dup, no dup, file dup, no file dup, both dups, skipped repos, combined errors |
| TestFullValidationPipeline | 5 | Valid+no dup, valid+txn dup, valid+file dup, invalid+dup, invalid+both dups |
| TestValidationResult | 4 | is_valid true/false, errors collection, error context values |
| **New Total** | **18** | **All duplicate scenarios** |
| **Cumulative** | **42** | **test_validator.py total** |
| **Full Suite** | **267** | **No regressions** |

## Deviations from Plan

None - plan executed exactly as written.

## Threat Mitigations Applied

| Threat ID | Mitigation | Status |
|-----------|-----------|--------|
| T-05-05 | Detect duplicate transactions by identify+reconciliationDate+trace | ✅ Implemented in _check_transaction_duplicate() |
| T-05-06 | Detect duplicate files by SHA256 hash | ✅ Implemented in _check_file_duplicate() |
| T-05-07 | Query uses indexed fields (idx_identify_date + idx_trace) | ✅ find_by_duplicate_key uses compound query on indexed fields |
| T-05-08 | Repository injection via constructor (not global state) | ✅ Validator constructor accepts optional repos |

## Known Stubs

None — all duplicate detection methods are fully implemented with wired repository interfaces.

## Success Criteria Verification

- [x] DataContainerRepository.find_by_duplicate_key implemented with correct query (identify + reconciliationDate + partnerData.trace)
- [x] Validator constructor accepts optional DataContainerRepository and ReconciliationFileRepository
- [x] validate_with_duplicates() async method runs core validation + duplicate checks
- [x] Transaction duplicate detected via identify + reconciliationDate + trace
- [x] File duplicate detected via fileHash
- [x] 42 total tests in test_validator.py (26 core + 16 new = exceeds 25+ minimum)
- [x] All 267 tests pass without MongoDB connection (mocked repositories)
- [x] ValidationResult correctly combines all errors (core + duplicate)

## Self-Check: PASSED

All created/modified files verified to exist. All commits verified in git log.
