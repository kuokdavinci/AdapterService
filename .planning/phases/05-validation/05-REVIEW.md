---
phase: 05-validation
reviewed: 2026-05-27T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - src/models/data_container.py
  - src/validators/__init__.py
  - src/validators/validator.py
  - tests/test_models.py
  - tests/test_validator.py
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 05: Code Review Report

**Reviewed:** 2026-05-27T00:00:00Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed 5 source files implementing the validation layer for CanonicalTransaction processing. The validator, data models, and test suite are well-structured with clear separation of concerns. The error-collection pattern (never fail-fast) is consistently applied. Two warnings were found: a potential TypeError in amount validation that contradicts the class's "never raises exceptions" guarantee, and a misleading test name that doesn't match its actual behavior. Three info-level suggestions address documentation accuracy and test code duplication.

## Warnings

### WR-01: Amount comparison can raise TypeError, violating "never raises exceptions" contract

**File:** `src/validators/validator.py:230`
**Issue:** The `_validate_decimal` method performs `if txn.amount < 0:` which will raise a `TypeError` if `txn.amount` is `None`. The class docstring (lines 42-43) explicitly states "Never raises exceptions — all errors are collected as ValidationError objects." While pydantic enforces that `amount` is required in `CanonicalTransaction`, the validator should defensively handle `None` to uphold its contract, especially since the same pattern is used for other fields (e.g., `txn.id is None` check at line 201).

**Fix:**
```python
def _validate_decimal(
    self,
    txn: CanonicalTransaction,
    result: ValidationResult,
    row_number: Optional[int],
    trace: Optional[str],
) -> None:
    if txn.amount is None:
        result.errors.append(ValidationError(
            field="amount",
            reason="required field 'amount' is missing",
            row=row_number,
            trace=trace,
        ))
        return

    if txn.amount < 0:
        result.errors.append(ValidationError(
            field="amount",
            reason=f"amount must be non-negative, got {txn.amount}",
            row=row_number,
            trace=trace,
        ))
```

### WR-02: Test name does not match test behavior

**File:** `tests/test_validator.py:57-68`
**Issue:** The test `test_missing_amount_produces_error` claims to test that a missing amount produces a validation error, but it actually constructs a valid transaction with a valid amount and asserts `result.is_valid is True`. The comment acknowledges "We can't actually construct a CanonicalTransaction without amount because pydantic enforces it," but the test name is misleading — it suggests the test verifies error production when it verifies the opposite. This could confuse future maintainers about what behavior is actually covered.

**Fix:** Rename the test to reflect what it actually tests, or remove it if redundant:
```python
# Option 1: Rename to match behavior
def test_valid_amount_present_no_error(self):
    """CanonicalTransaction with valid amount → no validation error."""
    ...

# Option 2: Remove entirely (covered by test_valid_transaction_passes)
```

## Info

### IN-01: Docstring claims amount/status presence checks that don't exist

**File:** `src/validators/validator.py:197-198`
**Issue:** The docstring for `_validate_required_fields` states: "Required fields: id (non-empty string), amount (present), currency (non-empty string), status (present)." However, the method body only checks `id` and `currency`. Amount and status presence are enforced by pydantic, not by this method. The docstring is misleading about what this method actually validates.

**Fix:**
```python
"""Check that all required fields are present and non-empty.

Required fields checked here: id (non-empty string), currency (non-empty string).
Note: amount and status presence are enforced by CanonicalTransaction's pydantic model.
"""
```

### IN-02: Duplicated _make_valid_txn helper across test classes

**File:** `tests/test_validator.py:299-308, 547-556`
**Issue:** The `_make_valid_txn` helper method is duplicated in both `TestDuplicateDetection` and `TestFullValidationPipeline` classes. While class-level helpers provide isolation, this duplication means changes to the default valid transaction must be made in multiple places.

**Fix:** Extract to module level (alongside the existing `_make_valid_txn` at line 15):
```python
# Module-level helper (already exists at line 15)
def _make_valid_txn(**overrides: dict) -> CanonicalTransaction:
    ...

# In test classes, use the module-level function directly
txn = _make_valid_txn()  # instead of self._make_valid_txn()
```

### IN-03: Status validation error message would be confusing for None

**File:** `src/validators/validator.py:272-275`
**Issue:** If `txn.status` were somehow `None` (pydantic prevents this, but defensive coding), the error message would read: `"invalid status value 'None' — must be one of SUCCESS, FAILED, PENDING, REVERSED"`. While technically correct, including `None` in the error message is less helpful than explicitly stating the status is missing.

**Fix:**
```python
def _validate_status(self, txn, result, row_number, trace) -> None:
    if txn.status is None:
        result.errors.append(ValidationError(
            field="status",
            reason="required field 'status' is missing",
            row=row_number,
            trace=trace,
        ))
        return

    if txn.status not in TransactionStatus:
        result.errors.append(ValidationError(
            field="status",
            reason=f"invalid status value '{txn.status}' — must be one of {', '.join(s.value for s in TransactionStatus)}",
            row=row_number,
            trace=trace,
        ))
```

---

_Reviewed: 2026-05-27T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
