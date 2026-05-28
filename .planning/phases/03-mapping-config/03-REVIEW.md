---
phase: 03-mapping-config
reviewed: 2026-05-27T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - pyproject.toml
  - src/config/cache.py
  - src/config/__init__.py
  - src/config/loader.py
  - src/config/validator.py
  - tests/test_config_cache.py
  - tests/test_config_loader.py
  - tests/test_config_validator.py
findings:
  critical: 0
  warning: 2
  info: 4
  total: 6
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-05-27T00:00:00Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Phase 03 introduces the mapping configuration engine — a TTL-based cache (`ConfigCache`), a field mapping validator (`ConfigValidator`), and an orchestrating loader (`ConfigLoader`) that integrates MongoDB repository access with caching and validation. The code is well-structured with dependency injection, thread-safe caching, and comprehensive test coverage.

Two warnings were identified: one related to potential race conditions in the cache's lazy cleanup pattern and one related to the validator's column format check not normalizing the stored value. Four informational suggestions cover minor improvements in test organization, error message consistency, and documentation.

## Warnings

### WR-01: Cache lazy cleanup does not prevent stale reads under concurrent access

**File:** `src/config/cache.py:43-53`
**Issue:** The `get()` method performs lazy cleanup of expired entries inside a lock, which is correct for thread safety. However, the `put()` method at line 64 also holds the lock while computing `expires_at` outside the lock (line 63). If `datetime.now(timezone.utc)` is called outside the lock and then the lock is acquired, there's a tiny window where the expiry time doesn't match the actual insertion time. This is a minor concern but could lead to inconsistent TTL behavior under high concurrency.

**Fix:**
```python
def put(self, key: str, config: MappingConfig, ttl_seconds: int = DEFAULT_TTL) -> None:
    """Store a MappingConfig with TTL-based expiration."""
    with self._lock:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        self._store[key] = CacheEntry(config=config, expires_at=expires_at)
```

Move the `expires_at` computation inside the lock to ensure atomicity of the timestamp and insertion.

### WR-02: ConfigValidator column format check does not normalize the column value

**File:** `src/config/validator.py:98-105`
**Issue:** The validator checks if `fm.column.upper()` matches the pattern but does not raise an error if the original value is lowercase — it just silently accepts it. While the test at `tests/test_config_validator.py:241-253` confirms this is intentional ("case-insensitive per plan"), the downstream code that uses `fm.column` will still see the lowercase value. If any code expects uppercase columns (e.g., for Excel cell references), this could cause subtle bugs.

**Fix:** Either (a) normalize the column to uppercase in the validator and return the normalized config, or (b) document clearly that callers must use `.upper()` when consuming the column value. If option (a):

```python
# In ConfigValidator.validate(), after the column format check:
if fm.column is not None:
    col_upper = fm.column.upper()
    if not ConfigValidator.COLUMN_PATTERN.match(col_upper):
        errors.append(...)
    # Optionally normalize: fm.column = col_upper  # Requires mutable config or return normalized copy
```

Alternatively, add a Pydantic validator on `FieldMapping.column` to normalize on input:

```python
# In src/core/types.py, FieldMapping class:
@field_validator("column", mode="before")
@classmethod
def normalize_column(cls, v: Optional[str]) -> Optional[str]:
    return v.upper() if v else v
```

## Info

### IN-01: ConfigValidationError uses Pydantic BaseModel instead of dataclass

**File:** `src/config/validator.py:15-20`
**Issue:** `ConfigValidationError` extends `Pydantic BaseModel` while `ConfigLoadError` (in `loader.py:20`) uses a `dataclass`. This inconsistency adds unnecessary Pydantic overhead for a simple error container. A `dataclass` would be sufficient and consistent with `ConfigLoadError`.

**Fix:**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ConfigValidationError:
    field: str
    reason: str
    config_version: Optional[str] = None
```

### IN-02: Test helper functions duplicated across test files

**File:** `tests/test_config_cache.py:15-32`, `tests/test_config_loader.py:16-29`, `tests/test_config_validator.py:13-22`
**Issue:** Each test file defines its own `_make_config()` helper with slightly different signatures. This leads to duplication and potential inconsistency. A shared conftest.py fixture would reduce duplication.

**Fix:** Create `tests/conftest.py` with shared fixtures:
```python
import pytest
from src.core.enums import FileType
from src.core.types import FieldMapping, FieldMappingType
from src.models.mapping_config import MappingConfig

@pytest.fixture
def valid_config():
    return MappingConfig(
        partner="MOMO",
        workflow_type="UPC",
        file_type=FileType.SETTLEMENT,
        sheet_name="Sheet1",
        field_mappings=[
            FieldMapping(path="amount", column="D", type=FieldMappingType.DECIMAL, required=True),
            FieldMapping(path="currency", constant="VND", type=FieldMappingType.CONSTANT),
            FieldMapping(path="status", column="F", type=FieldMappingType.STRING),
        ],
        config_version="v1.0",
    )
```

### IN-03: pyproject.toml has duplicate dev dependency definitions

**File:** `pyproject.toml:19-22, 31-33`
**Issue:** Dev dependencies are defined in both `[project.optional-dependencies]` (pytest, pytest-cov) and `[dependency-groups]` (pytest-asyncio). While these serve different purposes (optional extras vs dependency groups per PEP 735), having pytest-related packages split between them may cause confusion. Consider consolidating.

**Fix:**
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-asyncio>=1.4.0",
]
```

Or use only `[dependency-groups]` if that's the preferred approach for the project.

### IN-04: Missing type hints on private cache methods

**File:** `src/config/cache.py:34-35`
**Issue:** The `_store` attribute is typed as `dict[str, CacheEntry]` but `_lock` has no type annotation. Adding `self._lock: threading.Lock = threading.Lock()` would improve type clarity.

**Fix:**
```python
def __init__(self) -> None:
    self._store: dict[str, CacheEntry] = {}
    self._lock: threading.Lock = threading.Lock()
```

---

_Reviewed: 2026-05-27T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
