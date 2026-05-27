"""Core normalization engine for the reconciliation ingestion platform.

Transforms partner-specific row dictionaries into canonical field values
using FieldMapping rules, collecting all validation errors rather than
failing fast.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from src.core.constants import DEFAULT_CURRENCY
from src.core.enums import TransactionStatus
from src.core.types import FieldMapping, FieldMappingType, ValidationError


@dataclass
class NormalizationResult:
    """Result of a single row normalization.

    Attributes:
        data: Successfully normalized canonical field values keyed by path.
        errors: All conversion/validation errors encountered during normalization.
    """

    data: dict[str, Any] = field(default_factory=dict)
    errors: list[ValidationError] = field(default_factory=list)


class TransactionNormalizer:
    """Applies FieldMapping rules to raw row dictionaries.

    Performs type conversions (STRING, DECIMAL, DATE, CONSTANT) and
    collects validation errors. Never raises exceptions — all errors
    are collected as ValidationError objects.
    """

    _DATE_FORMATS = (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
    )

    def __init__(self, field_mappings: list[FieldMapping]) -> None:
        """Initialize with a list of field mappings.

        Args:
            field_mappings: List of FieldMapping rules to apply during normalization.

        Raises:
            ValueError: If field_mappings is empty.
        """
        if not field_mappings:
            raise ValueError("field_mappings must not be empty")
        self._field_mappings = field_mappings

    def normalize(
        self,
        row: dict[str, Any],
        row_number: Optional[int] = None,
    ) -> NormalizationResult:
        """Normalize a single row dictionary against configured field mappings.

        Args:
            row: Raw row dictionary keyed by column letter or source field name.
            row_number: Optional row number for error context.

        Returns:
            NormalizationResult with successfully converted data and any errors.
        """
        result = NormalizationResult(data={}, errors=[])

        for fm in self._field_mappings:
            value: Any = None
            error: Optional[ValidationError] = None

            # Resolve source value from row (skip for CONSTANT)
            if fm.type == FieldMappingType.CONSTANT:
                value, error = self._convert_constant(fm, row_number)
            else:
                source_value = self._resolve_source(row, fm)
                if isinstance(source_value, ValidationError):
                    result.errors.append(source_value)
                    continue
                if source_value is None:
                    # Value is None/empty — produce error
                    error = ValidationError(
                        field=fm.path,
                        reason="source field not found in row",
                        row=row_number,
                    )
                    result.errors.append(error)
                    continue

                # Apply type-specific conversion
                if fm.type == FieldMappingType.STRING:
                    value, error = self._convert_string(source_value, fm, row_number)
                elif fm.type == FieldMappingType.DECIMAL:
                    value, error = self._convert_decimal(source_value, fm, row_number)
                elif fm.type == FieldMappingType.DATE:
                    value, error = self._convert_date(source_value, fm, row_number)
                else:
                    # MAPPING type — deferred to Plan 02
                    error = ValidationError(
                        field=fm.path,
                        reason=f"mapping type not yet implemented for {fm.path}",
                        row=row_number,
                    )

            if error is not None:
                result.errors.append(error)
            elif value is not None:
                result.data[fm.path] = value

        return result

    def _resolve_source(
        self,
        row: dict[str, Any],
        fm: FieldMapping,
    ) -> Any | ValidationError | None:
        """Resolve the source value from the row dictionary.

        Column letter takes precedence over sourceField if both are set.

        Returns:
            The resolved value, a ValidationError if resolution fails, or None
            if the value itself is None/empty (caller should produce error).
        """
        if fm.column is not None:
            if fm.column not in row:
                return ValidationError(
                    field=fm.path,
                    reason=f"source field not found in row (column {fm.column})",
                )
            return row[fm.column]

        if fm.sourceField is not None:
            if fm.sourceField not in row:
                return ValidationError(
                    field=fm.path,
                    reason=f"source field not found in row (field {fm.sourceField})",
                )
            return row[fm.sourceField]

        # No column and no sourceField configured for non-CONSTANT mapping
        return ValidationError(
            field=fm.path,
            reason="no column or sourceField configured",
        )

    @staticmethod
    def _convert_string(
        value: Any,
        fm: FieldMapping,
        row_number: Optional[int],
    ) -> tuple[str | None, ValidationError | None]:
        """Convert value to string.

        None or empty string values produce a ValidationError.
        """
        if value is None:
            return None, ValidationError(
                field=fm.path,
                reason="value is None",
                row=row_number,
            )

        str_value = str(value)
        if str_value == "":
            return None, ValidationError(
                field=fm.path,
                reason="value is empty string",
                row=row_number,
            )

        return str_value, None

    @staticmethod
    def _convert_decimal(
        value: Any,
        fm: FieldMapping,
        row_number: Optional[int],
    ) -> tuple[Decimal | None, ValidationError | None]:
        """Convert value to Decimal.

        Float input is explicitly rejected. Invalid strings produce
        ValidationError with description of the failure.
        """
        if value is None:
            return None, ValidationError(
                field=fm.path,
                reason="value is None",
                row=row_number,
            )

        if isinstance(value, float):
            return None, ValidationError(
                field=fm.path,
                reason="float not allowed for monetary values",
                row=row_number,
            )

        try:
            return Decimal(str(value)), None
        except (InvalidOperation, ValueError) as exc:
            return None, ValidationError(
                field=fm.path,
                reason=f"invalid decimal value: {value!r}",
                row=row_number,
            )

    def _convert_date(
        self,
        value: Any,
        fm: FieldMapping,
        row_number: Optional[int],
    ) -> tuple[datetime | None, ValidationError | None]:
        """Convert value to datetime.

        Already datetime objects are returned as-is. String values are
        parsed against a whitelist of 4 date formats. Unmatched formats
        produce ValidationError.
        """
        if value is None:
            return None, ValidationError(
                field=fm.path,
                reason="value is None",
                row=row_number,
            )

        if isinstance(value, datetime):
            return value, None

        if not isinstance(value, str):
            return None, ValidationError(
                field=fm.path,
                reason=f"expected string or datetime, got {type(value).__name__}",
                row=row_number,
            )

        for fmt in self._DATE_FORMATS:
            try:
                return datetime.strptime(value, fmt), None
            except ValueError:
                continue

        return None, ValidationError(
            field=fm.path,
            reason=f"invalid date value: {value!r} (tried formats: {', '.join(self._DATE_FORMATS)})",
            row=row_number,
        )

    @staticmethod
    def _convert_constant(
        fm: FieldMapping,
        row_number: Optional[int],
    ) -> tuple[str | None, ValidationError | None]:
        """Return the configured constant value.

        None or empty constant produces ValidationError.
        """
        if fm.constant is None or fm.constant == "":
            return None, ValidationError(
                field=fm.path,
                reason="constant value is not configured",
                row=row_number,
            )

        return fm.constant, None
