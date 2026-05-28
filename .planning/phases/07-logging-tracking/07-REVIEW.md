---
phase: 07-logging-tracking
reviewed: 2026-05-28T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - src/logging/__init__.py
  - src/logging/logger.py
  - src/pipeline/ingestion_pipeline.py
  - tests/test_ingestion_pipeline.py
  - tests/test_logger.py
findings:
  critical: 0
  warning: 5
  info: 7
  total: 12
status: issues_found
---

# Phase 07: Code Review Report

**Reviewed:** 2026-05-28T00:00:00Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed 5 source files from Phase 07 (logging-tracking): the structured logging module (`src/logging/`), the ingestion pipeline (`src/pipeline/ingestion_pipeline.py`), and their corresponding test files. The logging module is well-structured with good security practices (field sanitization, type preservation). The ingestion pipeline has several issues around blocking I/O in async methods and platform-dependent path handling. Tests are comprehensive but have some inconsistencies in patterns.

No critical security vulnerabilities found. Five warnings identified, primarily around async correctness and cross-platform compatibility.

## Warnings

### WR-01: Blocking synchronous I/O in async method

**File:** `src/pipeline/ingestion_pipeline.py:73-81`
**Issue:** `_compute_file_hash` uses synchronous `open()` and `f.read()` inside an `async` method. For large Excel files, this will block the event loop and degrade concurrency.

**Fix:**
```python
import asyncio

def _compute_file_hash(self, file_path: str) -> str:
    import hashlib

    def _hash_sync():
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    return asyncio.get_event_loop().run_in_executor(None, _hash_sync)
```

Or make it `async def` and use `aiofiles`:
```python
async def _compute_file_hash(self, file_path: str) -> str:
    import hashlib
    import aiofiles

    sha256 = hashlib.sha256()
    async with aiofiles.open(file_path, "rb") as f:
        while chunk := await f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()
```

### WR-02: Platform-dependent path splitting

**File:** `src/pipeline/ingestion_pipeline.py:149`
**Issue:** `file_name = file_path.split("/")[-1]` assumes Unix-style forward slashes. On Windows, paths use backslashes, so this would return the full path instead of just the filename.

**Fix:**
```python
from pathlib import Path

file_name = Path(file_path).name
```

Or use `os.path.basename`:
```python
import os

file_name = os.path.basename(file_path)
```

### WR-03: Singleton not thread-safe

**File:** `src/logging/logger.py:199-204`
**Issue:** `get_structured_logger()` uses a simple `if _logger is None` check without synchronization. In a multi-threaded context (e.g., thread pool executors), two threads could both see `_logger is None` and create separate instances, breaking the singleton guarantee.

**Fix:**
```python
import threading

_lock = threading.Lock()

def get_structured_logger(name: str = "reconciliation") -> StructuredLogger:
    global _logger
    if _logger is None:
        with _lock:
            if _logger is None:  # Double-check after acquiring lock
                _logger = StructuredLogger(name=name)
    return _logger
```

### WR-04: Local imports inside methods

**File:** `src/pipeline/ingestion_pipeline.py:73, 84, 119-123`
**Issue:** `hashlib`, `string`, `TransactionNormalizer`, `ExcelStreamReader`, and `Validator` are imported inside methods. While this may help with circular imports, it obscures dependencies and makes the module harder to analyze. Each call re-executes the import machinery (though Python caches modules, the lookup still has overhead).

**Fix:** Move all imports to module level unless there is a documented circular import reason:
```python
# At top of file
import hashlib
import string
from src.normalizer.normalizer import TransactionNormalizer
from src.readers.excel_reader import ExcelStreamReader
from src.validators.validator import Validator
```

### WR-05: `emit_row_failed` called with empty trace for normalization/build errors

**File:** `src/pipeline/ingestion_pipeline.py:177-182, 191-196`
**Issue:** When normalization or canonical build fails, `emit_row_failed` is called with an empty string `""` for the `trace` parameter. The trace field is important for correlating row-level errors with specific transactions. An empty trace makes debugging harder.

**Fix:** Pass a synthetic trace or row identifier:
```python
self._logger.emit_row_failed(
    str(file_record.id),
    row_number,
    f"row:{row_number}",  # Synthetic trace instead of empty string
    norm_result.errors[0].reason,
)
```

## Info

### IN-01: `_default_serializer` is overly permissive

**File:** `src/logging/logger.py:52-56`
**Issue:** The JSON serializer fallback converts ANY object with `__str__` to a string. This could mask serialization issues and produce unexpected output for complex objects (e.g., database connections, file handles).

**Fix:** Be explicit about which types are handled:
```python
def _default_serializer(obj: Any) -> Any:
    if isinstance(obj, (Decimal,)):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "__uuid__"):  # UUID
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
```

### IN-02: `get_structured_logger` ignores `name` parameter after first call

**File:** `src/logging/logger.py:199-204`
**Issue:** If called with a different `name` after the singleton is created, the new name is silently ignored. This could confuse developers who expect different logger names.

**Fix:** Either document this behavior in the docstring or raise a warning/error if the name differs from the existing instance.

### IN-03: Bare except swallows secondary exceptions

**File:** `src/pipeline/ingestion_pipeline.py:258-259`
**Issue:** `except Exception: pass` silently swallows any errors during stats/status update in the exception handler. While marked as "Best effort", this could hide real issues like database connection failures.

**Fix:** At minimum, log the secondary exception:
```python
except Exception as update_err:
    self._logger.emit_file_failed(
        str(file_record.id),
        f"Failed to update stats after error: {update_err}",
    )
```

### IN-04: `process_file` method is very long (~200 lines)

**File:** `src/pipeline/ingestion_pipeline.py:120-270`
**Issue:** The `process_file` method has high cyclomatic complexity with many nested conditionals and a long linear flow. This makes it harder to test, review, and maintain.

**Fix:** Consider extracting row processing into a separate method:
```python
async def _process_row(self, row_dict, row_number, config, validator, ...):
    """Process a single row: normalize, validate, return DataContainer or error."""
    ...
```

### IN-05: Mixed temp file strategies in tests

**File:** `tests/test_ingestion_pipeline.py` (multiple locations)
**Issue:** Some tests use `tmp_path` fixture (pytest), others use `tempfile.NamedTemporaryFile` with manual cleanup. Should be consistent — `tmp_path` is cleaner and auto-cleans.

**Fix:** Standardize on `tmp_path`:
```python
async def test_process_file_all_rows_valid(self, tmp_path):
    file_path = tmp_path / "test.xlsx"
    wb = openpyxl.Workbook()
    ...
    wb.save(str(file_path))
    # No manual cleanup needed
```

### IN-06: `MockStructuredLogger` duplicates interface manually

**File:** `tests/test_ingestion_pipeline.py:19-34`
**Issue:** The mock class manually implements all logger methods. If `StructuredLogger` gains new emit methods, the mock must be updated manually.

**Fix:** Use `MagicMock` with `spec`:
```python
from unittest.mock import MagicMock
from src.logging import StructuredLogger

mock_logger = MagicMock(spec=StructuredLogger)
mock_logger.events = []
mock_logger.emit_row_success.side_effect = lambda *a: mock_logger.events.append(("ROW_SUCCESS", a))
```

### IN-07: Test helper doesn't restore handlers

**File:** `tests/test_logger.py:126-142`
**Issue:** `_capture_json_output` and `_capture_text_output` replace `logger._logger.handlers` but don't restore them after the test. While each test creates a new logger with a unique name (preventing cross-test pollution), this pattern is fragile and could cause issues if tests ever share logger instances.

**Fix:** Use a context manager or fixture:
```python
import contextlib

@contextlib.contextmanager
def capture_json_output(logger):
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter())
    old_handlers = logger._logger.handlers[:]
    logger._logger.handlers = [handler]
    try:
        yield stream
    finally:
        logger._logger.handlers = old_handlers
```

---

_Reviewed: 2026-05-28T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
