---
phase: 05-validation
fixed_at: 2026-05-27T00:10:00Z
review_path: .planning/phases/05-validation/05-REVIEW.md
iteration: 1
findings_in_scope: 2
fixed: 2
skipped: 0
status: all_fixed
---

# Phase 05: Code Review Fix Report

**Fixed at:** 2026-05-27T00:10:00Z
**Source review:** .planning/phases/05-validation/05-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 2
- Fixed: 2
- Skipped: 0

## Fixed Issues

### WR-01: Amount comparison can raise TypeError, violating "never raises exceptions" contract

**Files modified:** `src/validators/validator.py`
**Commit:** a125e85
**Applied fix:** Added a `None` guard at the start of `_validate_decimal` that checks `if txn.amount is None` before the `txn.amount < 0` comparison. If `amount` is `None`, a `ValidationError` is appended with reason `"required field 'amount' is missing"` and the method returns early. This upholds the class's "never raises exceptions" contract.

### WR-02: Test name does not match test behavior

**Files modified:** `tests/test_validator.py`
**Commit:** fe0254d
**Applied fix:** Renamed `test_missing_amount_produces_error` to `test_valid_amount_present_no_error` and simplified the docstring and body to reflect what the test actually does: constructs a valid transaction with a valid amount and asserts `result.is_valid is True`. Removed the misleading comments about pydantic enforcement since the test no longer claims to test missing-amount behavior.

---

_Fixed: 2026-05-27T00:10:00Z_
_Fixer: OpenCode (gsd-code-fixer)_
_Iteration: 1_
