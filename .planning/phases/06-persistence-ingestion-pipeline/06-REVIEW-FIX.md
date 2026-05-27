---
phase: 06-persistence-ingestion-pipeline
fixed_at: 2026-05-27T00:00:00Z
review_path: .planning/phases/06-persistence-ingestion-pipeline/06-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 06: Code Review Fix Report

**Fixed at:** 2026-05-27T00:00:00Z
**Source review:** .planning/phases/06-persistence-ingestion-pipeline/06-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 4
- Fixed: 4
- Skipped: 0

## Fixed Issues

### WR-01: `_flush_batch` return value ignored — `success_rows` could be inaccurate

**Files modified:** `src/pipeline/ingestion_pipeline.py`
**Commit:** f8830d1
**Applied fix:** Changed both the in-loop flush (line 299) and the final flush (line 305) to capture the return value from `_flush_batch()` and use it for `success_rows` instead of `len(batch_buffer)`. This ensures statistics reflect the actual number of documents inserted by the database.

### WR-02: `_compute_file_hash` hashes file path, not file content

**Files modified:** `src/pipeline/ingestion_pipeline.py`
**Commit:** f8830d1
**Applied fix:** Rewrote `_compute_file_hash()` to read the file content in 8KB chunks and compute SHA256 over the actual file data, rather than hashing the file path string. Updated docstring to reflect the new behavior.

### WR-03: `PartnerData` import inside the row processing loop

**Files modified:** `src/pipeline/ingestion_pipeline.py`
**Commit:** f8830d1
**Applied fix:** Added `PartnerData` to the existing module-level import from `src.models.data_container` (line 14) and removed the inline `from src.models.data_container import PartnerData` that was inside the `for row_tuple in reader.iter_rows():` loop.

### WR-04: Test name mismatch — `TestHappyPath` expects failed rows

**Files modified:** `tests/test_ingestion_integration.py`
**Commit:** 1a15cdf
**Applied fix:** Renamed test class from `TestHappyPath` to `TestStandardFile`, renamed method from `test_happy_path_all_valid_rows` to `test_standard_file_mixed_rows`, and updated class/method docstrings to accurately describe that the test processes a file with a mix of valid and invalid rows (8 success, 2 failed).

## Skipped Issues

None — all findings were fixed.

---

_Fixed: 2026-05-27T00:00:00Z_
_Fixer: OpenCode (gsd-code-fixer)_
_Iteration: 1_
