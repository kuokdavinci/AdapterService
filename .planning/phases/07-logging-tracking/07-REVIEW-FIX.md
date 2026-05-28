---
phase: 07-logging-tracking
fixed_at: 2026-05-28T00:00:00Z
review_path: .planning/phases/07-logging-tracking/07-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 07: Code Review Fix Report

**Fixed at:** 2026-05-28T00:00:00Z
**Source review:** .planning/phases/07-logging-tracking/07-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5
- Fixed: 5
- Skipped: 0

## Fixed Issues

### WR-01: Blocking synchronous I/O in async method

**Files modified:** `src/pipeline/ingestion_pipeline.py`
**Commit:** abb1db2
**Applied fix:** Changed `_compute_file_hash` from sync `def` to `async def`, wrapping the synchronous file I/O in a nested `_hash_sync()` function executed via `asyncio.get_running_loop().run_in_executor(None, _hash_sync)`. Updated the caller in `process_file` to `await` the method.

### WR-02: Platform-dependent path splitting

**Files modified:** `src/pipeline/ingestion_pipeline.py`
**Commit:** 573d762
**Applied fix:** Added `from pathlib import Path` to module-level imports. Replaced `file_path.split("/")[-1] if "/" in file_path else file_path` with `Path(file_path).name` for cross-platform filename extraction.

### WR-03: Singleton not thread-safe

**Files modified:** `src/logging/logger.py`
**Commit:** 54b3913
**Applied fix:** Added `import threading` and a module-level `_lock = threading.Lock()`. Updated `get_structured_logger()` to use double-checked locking pattern: outer `if _logger is None` check, then `with _lock:` with inner `if _logger is None` check. Added docstring note about name parameter behavior.

### WR-04: Local imports inside methods

**Files modified:** `src/pipeline/ingestion_pipeline.py`
**Commit:** d4882f7
**Applied fix:** Moved all local imports to module level: `asyncio`, `hashlib`, `string`, `TransactionNormalizer`, `ExcelStreamReader`, `Validator`. Removed unused `from datetime import datetime` local import. Removed corresponding local import statements from `_compute_file_hash`, `_tuple_to_dict`, and `process_file` methods.

### WR-05: `emit_row_failed` called with empty trace for normalization/build errors

**Files modified:** `src/pipeline/ingestion_pipeline.py`
**Commit:** a8a300f
**Applied fix:** Replaced empty string `""` trace argument with synthetic trace `f"row:{row_number}"` in two `emit_row_failed` calls: one for normalization errors and one for canonical build errors. This provides a correlatable identifier for debugging row-level failures.

---

_Fixed: 2026-05-28T00:00:00Z_
_Fixer: OpenCode (gsd-code-fixer)_
_Iteration: 1_
