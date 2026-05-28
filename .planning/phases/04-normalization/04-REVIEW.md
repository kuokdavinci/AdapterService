---
phase: 04-normalization
reviewed: 2026-05-27T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - src/normalizer/__init__.py
  - src/normalizer/normalizer.py
  - tests/test_normalizer.py
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-05-27T00:00:00Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Reviewed the normalization module (core normalizer engine and tests). The code is well-structured with good error-collection patterns (never fail-fast), comprehensive test coverage, and clean separation of concerns. Two warnings were identified around error message accuracy and exception handling completeness. Three info-level maintenance concerns were noted.

## Warnings

### WR-01: Misleading error message when source field exists but value is None

**File:** `src/normalizer/normalizer.py:87-95`
**Issue:** When `_resolve_source` returns `None` (key exists in row but value is `None`), the `normalize` method produces a `ValidationError` with reason `"source field not found in row"`. This is inaccurate — the field WAS found, its value is just `None`. This misleads debugging and log analysis.

The flow: `_resolve_source` returns `row[fm.column]` which can be `None` if the key exists with a `None` value. Then `normalize` line 87 checks `if source_value is None:` and produces the "not found" error.

**Fix:**
```python
# Line 89-93: Distinguish between missing key and None value
if source_value is None:
    error = ValidationError(
        field=fm.path,
        reason="source field value is None",  # Changed from "source field not found in row"
        row=row_number,
    )
```

### WR-02: Dead exception type in `_convert_decimal`

**File:** `src/normalizer/normalizer.py:217`
**Issue:** `Decimal(str(value))` raises `InvalidOperation` for invalid numeric strings, never `ValueError`. The `ValueError` in the except clause is unreachable dead code. While harmless, it suggests incomplete understanding of `Decimal`'s exception behavior and could mask future refactoring mistakes.

`Decimal.__new__` raises `decimal.InvalidOperation` for malformed strings. `str()` on any Python object never raises `ValueError`.

**Fix:**
```python
# Line 217: Remove unreachable ValueError
try:
    return Decimal(str(value)), None
except InvalidOperation as exc:
    return None, ValidationError(
        field=fm.path,
        reason=f"invalid decimal value: {value!r}",
        row=row_number,
    )
```

## Info

### IN-01: Hardcoded `canonical_keys` duplicates `CanonicalTransaction` schema

**File:** `src/normalizer/normalizer.py:367`
**Issue:** The set `{"id", "trace", "amount", "currency", "status", "transDate"}` is hardcoded and duplicates knowledge from the `CanonicalTransaction` model. If `CanonicalTransaction` gains or loses fields, this set must be manually updated, creating a maintenance coupling.

**Fix:** Derive from `CanonicalTransaction.model_fields` at runtime:
```python
canonical_keys = set(CanonicalTransaction.model_fields.keys())
```

### IN-02: Inconsistent `errors` list return behavior in `build_canonical`

**File:** `src/normalizer/normalizer.py:353, 364, 379`
**Issue:** When errors exist, `build_canonical` returns `errors + new_errors` (a new list). When successful, it returns the original `errors` list reference. This inconsistency means callers who mutate the returned list may or may not affect the original, depending on the code path.

**Fix:** Always return a new list for consistency:
```python
# Line 379: Return a copy instead of the original reference
return txn, list(errors)
```

### IN-03: `_convert_date` is not static while other converters are

**File:** `src/normalizer/normalizer.py:224`
**Issue:** `_convert_string`, `_convert_decimal`, `_convert_mapping`, and `_convert_constant` are all `@staticmethod`, but `_convert_date` is an instance method. It only accesses `self._DATE_FORMATS` (a class-level tuple), so it could be static too. This inconsistency is minor but worth noting for API uniformity.

**Fix:** Either make `_convert_date` a `@staticmethod` and pass formats as a parameter, or add a class-level constant accessible to static methods:
```python
# Option: Make static with class-level constant
@staticmethod
def _convert_date(value, fm, row_number):
    DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S")
    # ... rest of method using DATE_FORMATS
```

---

_Reviewed: 2026-05-27T00:00:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
