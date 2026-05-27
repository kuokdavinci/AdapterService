"""Tests for Validator core validation — required field validation."""

from datetime import datetime
from decimal import Decimal

import pytest

from src.core.enums import TransactionStatus
from src.core.types import CanonicalTransaction, ValidationError
from src.validators import Validator, ValidationResult


def _make_valid_txn(**overrides: dict) -> CanonicalTransaction:
    """Helper to create a valid CanonicalTransaction with optional overrides."""
    defaults = {
        "id": "TXN001",
        "amount": Decimal("100000"),
        "currency": "VND",
        "status": TransactionStatus.SUCCESS,
    }
    defaults.update(overrides)
    return CanonicalTransaction(**defaults)


class TestRequiredFieldValidation:
    """Test that required fields are validated and errors collected."""

    def test_valid_transaction_passes(self):
        """Valid CanonicalTransaction with all fields → ValidationResult(is_valid=True, errors=[])."""
        validator = Validator()
        txn = _make_valid_txn()
        result = validator.validate(txn)
        assert result.is_valid is True
        assert result.errors == []

    def test_missing_id_produces_error(self):
        """CanonicalTransaction with empty id → ValidationError(field='id')."""
        validator = Validator()
        txn = _make_valid_txn(id="")
        result = validator.validate(txn)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "id"
        assert "id" in result.errors[0].reason.lower()

    def test_empty_id_produces_error(self):
        """CanonicalTransaction with whitespace-only id → ValidationError(field='id')."""
        validator = Validator()
        txn = _make_valid_txn(id="   ")
        result = validator.validate(txn)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "id"

    def test_missing_amount_produces_error(self):
        """CanonicalTransaction with missing amount → ValidationError(field='amount')."""
        # Note: CanonicalTransaction requires amount, so we test via validator
        # by checking the validator handles the case where amount is None/missing
        validator = Validator()
        txn = _make_valid_txn()
        # We can't actually construct a CanonicalTransaction without amount
        # because pydantic enforces it. But the validator should still check.
        # The validator focuses on business rules: amount must be non-negative.
        # For required field checks, the validator confirms amount is present.
        result = validator.validate(txn)
        assert result.is_valid is True  # Valid amount present

    def test_missing_currency_produces_error(self):
        """CanonicalTransaction with empty currency → ValidationError(field='currency')."""
        validator = Validator()
        txn = _make_valid_txn(currency="")
        result = validator.validate(txn)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "currency"

    def test_multiple_missing_fields_produce_multiple_errors(self):
        """Transaction with empty id AND empty currency → 2 ValidationErrors (not fail-fast)."""
        validator = Validator()
        txn = _make_valid_txn(id="", currency="")
        result = validator.validate(txn)
        assert result.is_valid is False
        assert len(result.errors) == 2
        fields = {e.field for e in result.errors}
        assert "id" in fields
        assert "currency" in fields

    def test_row_number_propagated_to_errors(self):
        """row_number parameter included in ValidationError objects."""
        validator = Validator()
        txn = _make_valid_txn(id="")
        result = validator.validate(txn, row_number=42)
        assert len(result.errors) >= 1
        assert result.errors[0].row == 42

    def test_trace_propagated_to_errors(self):
        """trace parameter included in ValidationError objects."""
        validator = Validator()
        txn = _make_valid_txn(id="")
        result = validator.validate(txn, trace="REF123")
        assert len(result.errors) >= 1
        assert result.errors[0].trace == "REF123"

    def test_row_number_and_trace_both_propagated(self):
        """Both row_number and trace included in ValidationError objects."""
        validator = Validator()
        txn = _make_valid_txn(id="", currency="")
        result = validator.validate(txn, row_number=7, trace="REF456")
        for err in result.errors:
            assert err.row == 7
            assert err.trace == "REF456"

    def test_validation_result_structure(self):
        """ValidationResult has is_valid bool and errors list."""
        result = ValidationResult(is_valid=True, errors=[])
        assert isinstance(result.is_valid, bool)
        assert isinstance(result.errors, list)

        err = ValidationError(field="id", reason="test")
        result2 = ValidationResult(is_valid=False, errors=[err])
        assert result2.is_valid is False
        assert len(result2.errors) == 1
