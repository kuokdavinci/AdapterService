---
phase: 01-foundation
reviewed: 2026-05-27T16:00:00Z
depth: standard
files_reviewed: 24
files_reviewed_list:
  - .env.example
  - .gitignore
  - pyproject.toml
  - requirements.txt
  - src/__init__.py
  - src/config/__init__.py
  - src/config/settings.py
  - src/core/__init__.py
  - src/core/constants.py
  - src/core/enums.py
  - src/core/types.py
  - src/models/__init__.py
  - src/models/data_container.py
  - src/models/indexes.py
  - src/models/mapping_config.py
  - src/models/reconciliation_file.py
  - src/models/repository.py
  - tests/__init__.py
  - tests/test_core_types.py
  - tests/test_indexes.py
  - tests/test_models.py
  - tests/test_settings.py
findings:
  critical: 6
  warning: 1
  info: 10
  total: 17
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-05-27T16:00:00Z
**Depth:** standard
**Files Reviewed:** 24
**Status:** issues_found

## Summary

Phase 01 establishes the Python project structure with pydantic-based settings, core enums/types, MongoDB document models, a generic repository pattern, and comprehensive test suites (76 tests total across 4 test files). The overall architecture is sound — StrEnum usage, Decimal-enforced monetary amounts, camelCase aliases for MongoDB, and a generic BaseRepository are all good patterns.

However, there are **6 critical issues** — all involving MongoDB index field name mismatches. The index definitions in `src/models/indexes.py` use Python snake_case attribute names, but documents are stored in MongoDB with camelCase field names (via `model_dump(by_alias=True)`). This means indexes will be created on non-existent fields, leaving all queries unindexed and defeating the purpose of the index definitions.

## Critical Issues

### CR-01: Index `file_hash` should be `fileHash` (reconciliation_file)

**File:** `src/models/indexes.py:13`
**Issue:** The unique index on `file_hash` uses the Python attribute name, but MongoDB stores this field as `fileHash` (per `ReconciliationFile.file_hash: Field(alias="fileHash")`). The index will be created on a non-existent field, so duplicate detection queries on `fileHash` will not use this index.

**Fix:**
```python
# Change line 13 from:
IndexModel("file_hash", unique=True, name="idx_file_hash_unique"),
# To:
IndexModel("fileHash", unique=True, name="idx_file_hash_unique"),
```

### CR-02: Index `partner_data.trace` should be `partnerData.trace` (data_container)

**File:** `src/models/indexes.py:34`
**Issue:** `DataContainer.partner_data` has `alias="partnerData"`, so the nested field is stored as `partnerData.trace` in MongoDB, not `partner_data.trace`.

**Fix:**
```python
# Change line 34 from:
IndexModel("partner_data.trace", name="idx_trace"),
# To:
IndexModel("partnerData.trace", name="idx_trace"),
```

### CR-03: Index `reconciliation_date` should be `reconciliationDate` (data_container compound)

**File:** `src/models/indexes.py:38`
**Issue:** `DataContainer.reconciliation_date` has `alias="reconciliationDate"`. The compound index uses the Python name but MongoDB stores `reconciliationDate`.

**Fix:**
```python
# Change line 38 from:
[("identify", ASCENDING), ("reconciliation_date", ASCENDING)],
# To:
[("identify", ASCENDING), ("reconciliationDate", ASCENDING)],
```

### CR-04: Index `operation_status` should be `operationStatus` (data_container)

**File:** `src/models/indexes.py:42`
**Issue:** `DataContainer.operation_status` has `alias="operationStatus"`.

**Fix:**
```python
# Change line 42 from:
IndexModel("operation_status", name="idx_operation_status"),
# To:
IndexModel("operationStatus", name="idx_operation_status"),
```

### CR-05: Index `partner_data.status` should be `partnerData.status` (data_container)

**File:** `src/models/indexes.py:46`
**Issue:** Same as CR-02 — nested field uses Python name instead of MongoDB alias.

**Fix:**
```python
# Change line 46 from:
IndexModel("partner_data.status", name="idx_partner_status"),
# To:
IndexModel("partnerData.status", name="idx_partner_status"),
```

### CR-06: Index `source_file_id` should be `sourceFileId` (data_container)

**File:** `src/models/indexes.py:50`
**Issue:** `DataContainer.source_file_id` has `alias="sourceFileId"`. The repository method `find_by_source_file` queries `{"sourceFileId": ...}` but the index is on `source_file_id` — a different field.

**Fix:**
```python
# Change line 50 from:
IndexModel("source_file_id", name="idx_source_file"),
# To:
IndexModel("sourceFileId", name="idx_source_file"),
```

## Warnings

### WR-01: `MappingConfigRepository.find_by_version` queries non-existent field

**File:** `src/models/mapping_config.py:62-64`
**Issue:** The method queries `{"partner": partner, "configVersion": version}`, but the `MappingConfig` model has no `configVersion` or `config_version` field. This method will never return results. Either the field needs to be added to the model, or this method should be removed/renamed.

**Fix:** Either add the field to `MappingConfig`:
```python
# In MappingConfig model:
config_version: Optional[str] = Field(default=None, alias="configVersion")
```
Or remove the method if it's a stub for future use (add a `# TODO` comment).

## Info

### IN-01: Unused imports in test files

**File:** `tests/test_settings.py:3` — `import os` unused
**File:** `tests/test_core_types.py:3` — `InvalidOperation` unused
**File:** `tests/test_models.py:9` — `BsonDecimal128` unused
**File:** `tests/test_models.py:12` — `TransactionStatus` unused
**File:** `tests/test_models.py:6` — `AsyncMock` unused
**File:** `tests/test_indexes.py:5` — `import pytest` unused
**File:** `tests/test_indexes.py:8` — `DESCENDING` unused

**Fix:** Remove unused imports to keep code clean.

### IN-02: `LOG_FORMATS` constant defined but not used in production code

**File:** `src/core/constants.py:7`
**Issue:** `LOG_FORMATS = {"json", "text"}` is defined and tested but never consumed by any business logic. It's a stub for future use.

**Fix:** Either use it in settings validation (e.g., validate `log_format` against `LOG_FORMATS`) or add a `# TODO` comment to indicate it's planned.

### IN-03: `python-decouple` listed as dependency but not used

**File:** `pyproject.toml:15`, `requirements.txt:5`
**Issue:** `python-decouple>=3.8` is listed as a dependency but no code imports from `decouple`. Configuration is handled entirely by `pydantic-settings`.

**Fix:** Remove from both `pyproject.toml` and `requirements.txt`.

### IN-04: `PartnerData` defined in two places with different signatures

**File:** `src/core/types.py:63-84` and `src/models/data_container.py:19-49`
**Issue:** `PartnerData` exists in both `src/core/types.py` (with `transDate` field, no `model_config`) and `src/models/data_container.py` (with `trans_date` field + `alias="transDate"`, plus `model_config`). The models version is the one actually used (exported from `__init__.py`), but the core types version is a confusing duplicate.

**Fix:** Remove the `PartnerData` class from `src/core/types.py` since the MongoDB-specific version in `data_container.py` is the one in use. If a core/protocol-level PartnerData is needed, consider renaming to avoid confusion.

### IN-05: `Settings` instantiated at module load time

**File:** `src/config/settings.py:22`
**Issue:** `settings = Settings()` is evaluated at import time. This means environment variables must be set before the module is first imported. The test file works around this with `importlib.reload()`, but this pattern is fragile.

**Fix:** Consider lazy initialization or a factory function:
```python
_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

### IN-06: `mongodb_url` stored as plain string (noted as threat flag)

**File:** `src/config/settings.py:9`
**Issue:** Already flagged in the phase summary as `threat_flag:information_disclosure`. MongoDB connection strings often contain credentials. Using `SecretStr` from pydantic would prevent accidental logging/exposure.

**Fix:**
```python
from pydantic import SecretStr

mongodb_url: SecretStr = SecretStr("mongodb://localhost:27017")
```

### IN-07: Misleading comment in `BaseRepository.create()`

**File:** `src/models/repository.py:30`
**Issue:** Comment says "Convert UUID to string for MongoDB storage" but no explicit conversion occurs — pydantic's `model_dump()` handles UUID→string serialization automatically. The comment suggests manual conversion that doesn't exist.

**Fix:** Update or remove the comment:
```python
# model_dump serializes UUID to string automatically
data = doc.model_dump(by_alias=True, exclude_none=False)
```

### IN-08: `pytest` in main dependencies instead of dev-only

**File:** `requirements.txt:6`
**Issue:** `pytest>=7.0` is listed in the main `requirements.txt` alongside production dependencies. It's correctly in `[project.optional-dependencies] dev` in `pyproject.toml`, but the flat `requirements.txt` mixes dev and prod deps.

**Fix:** Remove `pytest` from `requirements.txt` or create a separate `requirements-dev.txt`.

---

_Reviewed: 2026-05-27T16:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
