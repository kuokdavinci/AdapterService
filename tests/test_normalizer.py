"""Tests for TransactionNormalizer core normalization engine."""

from datetime import datetime
from decimal import Decimal

import pytest

from src.core.types import FieldMapping, FieldMappingType, ValidationError
from src.normalizer import TransactionNormalizer, NormalizationResult


def _make_mapping(
    path: str,
    type: FieldMappingType,
    column: str | None = None,
    sourceField: str | None = None,
    constant: str | None = None,
) -> FieldMapping:
    """Helper to create FieldMapping instances for tests."""
    return FieldMapping(
        path=path,
        column=column,
        sourceField=sourceField,
        type=type,
        constant=constant,
    )


SAMPLE_ROW = {
    "A": "TXN001",
    "B": "100000",
    "C": "2024-01-15",
    "D": "Thành công",
}


class TestNormalizationResult:
    """Test NormalizationResult dataclass."""

    def test_empty_result(self):
        result = NormalizationResult(data={}, errors=[])
        assert result.data == {}
        assert result.errors == []

    def test_result_with_data_and_errors(self):
        err = ValidationError(field="amount", reason="invalid")
        result = NormalizationResult(
            data={"id": "TXN001"},
            errors=[err],
        )
        assert result.data == {"id": "TXN001"}
        assert len(result.errors) == 1
        assert result.errors[0].field == "amount"


class TestEmptyFieldMappings:
    """Test that empty field_mappings list is rejected."""

    def test_empty_mappings_raises_error(self):
        with pytest.raises(ValueError, match="field_mappings"):
            TransactionNormalizer(field_mappings=[])


class TestStringConversion:
    """Test STRING type conversion."""

    def test_valid_string_passthrough(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("id", FieldMappingType.STRING, column="A")]
        )
        result = normalizer.normalize({"A": "TXN001"})
        assert result.data["id"] == "TXN001"
        assert result.errors == []

    def test_numeric_value_converted_to_string(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("id", FieldMappingType.STRING, column="A")]
        )
        result = normalizer.normalize({"A": 12345})
        assert result.data["id"] == "12345"
        assert result.errors == []

    def test_none_value_produces_validation_error(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("id", FieldMappingType.STRING, column="A")]
        )
        result = normalizer.normalize({"A": None})
        assert "id" not in result.data
        assert len(result.errors) == 1
        assert result.errors[0].field == "id"

    def test_empty_string_produces_validation_error(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("id", FieldMappingType.STRING, column="A")]
        )
        result = normalizer.normalize({"A": ""})
        assert "id" not in result.data
        assert len(result.errors) == 1
        assert result.errors[0].field == "id"


class TestDecimalConversion:
    """Test DECIMAL type conversion."""

    def test_valid_integer_string_to_decimal(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("amount", FieldMappingType.DECIMAL, column="B")]
        )
        result = normalizer.normalize({"B": "100000"})
        assert result.data["amount"] == Decimal("100000")
        assert result.errors == []

    def test_valid_decimal_string_to_decimal(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("amount", FieldMappingType.DECIMAL, column="B")]
        )
        result = normalizer.normalize({"B": "99.99"})
        assert result.data["amount"] == Decimal("99.99")
        assert result.errors == []

    def test_float_input_produces_validation_error(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("amount", FieldMappingType.DECIMAL, column="B")]
        )
        result = normalizer.normalize({"B": 100.50})
        assert "amount" not in result.data
        assert len(result.errors) == 1
        assert "float" in result.errors[0].reason.lower()

    def test_invalid_string_produces_validation_error(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("amount", FieldMappingType.DECIMAL, column="B")]
        )
        result = normalizer.normalize({"B": "abc"})
        assert "amount" not in result.data
        assert len(result.errors) == 1
        assert result.errors[0].field == "amount"

    def test_none_value_produces_validation_error(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("amount", FieldMappingType.DECIMAL, column="B")]
        )
        result = normalizer.normalize({"B": None})
        assert "amount" not in result.data
        assert len(result.errors) == 1
        assert result.errors[0].field == "amount"


class TestDateConversion:
    """Test DATE type conversion."""

    def test_iso_format_date(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("transDate", FieldMappingType.DATE, column="C")]
        )
        result = normalizer.normalize({"C": "2024-01-15"})
        assert result.data["transDate"] == datetime(2024, 1, 15)
        assert result.errors == []

    def test_dd_mm_yyyy_format_date(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("transDate", FieldMappingType.DATE, column="C")]
        )
        result = normalizer.normalize({"C": "15/01/2024"})
        assert result.data["transDate"] == datetime(2024, 1, 15)
        assert result.errors == []

    def test_iso_format_with_time(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("transDate", FieldMappingType.DATE, column="C")]
        )
        result = normalizer.normalize({"C": "2024-01-15 10:30:00"})
        assert result.data["transDate"] == datetime(2024, 1, 15, 10, 30, 0)
        assert result.errors == []

    def test_dd_mm_yyyy_with_time(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("transDate", FieldMappingType.DATE, column="C")]
        )
        result = normalizer.normalize({"C": "15/01/2024 10:30:00"})
        assert result.data["transDate"] == datetime(2024, 1, 15, 10, 30, 0)
        assert result.errors == []

    def test_datetime_passed_through_as_is(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("transDate", FieldMappingType.DATE, column="C")]
        )
        original = datetime(2024, 3, 20)
        result = normalizer.normalize({"C": original})
        assert result.data["transDate"] is original
        assert result.errors == []

    def test_invalid_string_produces_validation_error(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("transDate", FieldMappingType.DATE, column="C")]
        )
        result = normalizer.normalize({"C": "not-a-date"})
        assert "transDate" not in result.data
        assert len(result.errors) == 1
        assert result.errors[0].field == "transDate"

    def test_none_value_produces_validation_error(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("transDate", FieldMappingType.DATE, column="C")]
        )
        result = normalizer.normalize({"C": None})
        assert "transDate" not in result.data
        assert len(result.errors) == 1
        assert result.errors[0].field == "transDate"


class TestConstantConversion:
    """Test CONSTANT type conversion."""

    def test_valid_constant_returned(self):
        normalizer = TransactionNormalizer(
            field_mappings=[
                _make_mapping("currency", FieldMappingType.CONSTANT, constant="VND")
            ]
        )
        result = normalizer.normalize({})
        assert result.data["currency"] == "VND"
        assert result.errors == []

    def test_none_constant_produces_error(self):
        normalizer = TransactionNormalizer(
            field_mappings=[
                _make_mapping("currency", FieldMappingType.CONSTANT, constant=None)
            ]
        )
        result = normalizer.normalize({})
        assert "currency" not in result.data
        assert len(result.errors) == 1
        assert result.errors[0].field == "currency"


class TestSourceFieldResolution:
    """Test source field resolution by column and sourceField."""

    def test_resolve_by_column_letter(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("id", FieldMappingType.STRING, column="A")]
        )
        result = normalizer.normalize({"A": "TXN001"})
        assert result.data["id"] == "TXN001"

    def test_resolve_by_source_field(self):
        normalizer = TransactionNormalizer(
            field_mappings=[
                _make_mapping("id", FieldMappingType.STRING, sourceField="txn_id")
            ]
        )
        result = normalizer.normalize({"txn_id": "TXN002"})
        assert result.data["id"] == "TXN002"

    def test_column_takes_precedence_over_source_field(self):
        normalizer = TransactionNormalizer(
            field_mappings=[
                _make_mapping(
                    "id", FieldMappingType.STRING, column="A", sourceField="txn_id"
                )
            ]
        )
        result = normalizer.normalize({"A": "FROM_COL", "txn_id": "FROM_SOURCE"})
        assert result.data["id"] == "FROM_COL"

    def test_missing_column_key_produces_error(self):
        normalizer = TransactionNormalizer(
            field_mappings=[_make_mapping("id", FieldMappingType.STRING, column="Z")]
        )
        result = normalizer.normalize({"A": "TXN001"})
        assert "id" not in result.data
        assert len(result.errors) == 1
        assert "not found" in result.errors[0].reason.lower()

    def test_missing_source_field_key_produces_error(self):
        normalizer = TransactionNormalizer(
            field_mappings=[
                _make_mapping("id", FieldMappingType.STRING, sourceField="missing_key")
            ]
        )
        result = normalizer.normalize({"A": "TXN001"})
        assert "id" not in result.data
        assert len(result.errors) == 1
        assert "not found" in result.errors[0].reason.lower()

    def test_no_column_and_no_source_field_produces_error(self):
        normalizer = TransactionNormalizer(
            field_mappings=[
                _make_mapping("id", FieldMappingType.STRING)
            ]
        )
        result = normalizer.normalize({"A": "TXN001"})
        assert "id" not in result.data
        assert len(result.errors) == 1
        assert "no column" in result.errors[0].reason.lower()

    def test_constant_skips_row_lookup(self):
        normalizer = TransactionNormalizer(
            field_mappings=[
                _make_mapping("currency", FieldMappingType.CONSTANT, constant="VND")
            ]
        )
        # Empty row — should still work for CONSTANT
        result = normalizer.normalize({})
        assert result.data["currency"] == "VND"
        assert result.errors == []


class TestErrorCollection:
    """Test that multiple errors are collected (not fail-fast)."""

    def test_multiple_errors_collected(self):
        normalizer = TransactionNormalizer(
            field_mappings=[
                _make_mapping("id", FieldMappingType.STRING, column="A"),
                _make_mapping("amount", FieldMappingType.DECIMAL, column="B"),
                _make_mapping("transDate", FieldMappingType.DATE, column="C"),
            ]
        )
        result = normalizer.normalize({"A": None, "B": "abc", "C": "not-a-date"})
        assert len(result.errors) == 3
        assert result.data == {}

    def test_successful_fields_in_data_with_other_errors(self):
        normalizer = TransactionNormalizer(
            field_mappings=[
                _make_mapping("id", FieldMappingType.STRING, column="A"),
                _make_mapping("amount", FieldMappingType.DECIMAL, column="B"),
            ]
        )
        result = normalizer.normalize({"A": "TXN001", "B": "abc"})
        assert result.data["id"] == "TXN001"
        assert "amount" not in result.data
        assert len(result.errors) == 1

    def test_row_number_propagated_to_errors(self):
        normalizer = TransactionNormalizer(
            field_mappings=[
                _make_mapping("id", FieldMappingType.STRING, column="A"),
                _make_mapping("amount", FieldMappingType.DECIMAL, column="B"),
            ]
        )
        result = normalizer.normalize({"A": None, "B": None}, row_number=42)
        assert len(result.errors) == 2
        for err in result.errors:
            assert err.row == 42


class TestFullNormalization:
    """Test full normalization with multiple field types."""

    def test_full_sample_row(self):
        normalizer = TransactionNormalizer(
            field_mappings=[
                _make_mapping("id", FieldMappingType.STRING, column="A"),
                _make_mapping("amount", FieldMappingType.DECIMAL, column="B"),
                _make_mapping("transDate", FieldMappingType.DATE, column="C"),
                _make_mapping("currency", FieldMappingType.CONSTANT, constant="VND"),
            ]
        )
        result = normalizer.normalize(SAMPLE_ROW)
        assert result.data["id"] == "TXN001"
        assert result.data["amount"] == Decimal("100000")
        assert result.data["transDate"] == datetime(2024, 1, 15)
        assert result.data["currency"] == "VND"
        assert result.errors == []
