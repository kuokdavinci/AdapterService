"""Core Validator service for CanonicalTransaction validation.

Validates CanonicalTransaction objects against business rules:
- Required field checks (id, amount, currency, status)
- Decimal validation (non-negative)
- Date validation (type integrity)
- Status validation (enum membership)

Collects ALL errors — never fail-fast.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

from src.core.enums import TransactionStatus
from src.core.types import CanonicalTransaction, ValidationError


@dataclass
class ValidationResult:
    """Result of validating a CanonicalTransaction.

    Attributes:
        is_valid: True if no validation errors were found.
        errors: All validation errors encountered during validation.
    """

    is_valid: bool = True
    errors: list[ValidationError] = field(default_factory=list)


class Validator:
    """Validates CanonicalTransaction objects against business rules.

    Never raises exceptions — all errors are collected as ValidationError
    objects. Multiple errors are collected (not fail-fast).
    """

    def validate(
        self,
        txn: CanonicalTransaction,
        row_number: Optional[int] = None,
        trace: Optional[str] = None,
    ) -> ValidationResult:
        """Validate a CanonicalTransaction against all business rules.

        Args:
            txn: The canonical transaction to validate.
            row_number: Optional row number for error context.
            trace: Optional trace identifier for error context.

        Returns:
            ValidationResult with is_valid flag and collected errors.
        """
        result = ValidationResult(is_valid=True, errors=[])

        self._validate_required_fields(txn, result, row_number, trace)
        self._validate_decimal(txn, result, row_number, trace)
        self._validate_date(txn, result, row_number, trace)

        result.is_valid = len(result.errors) == 0
        return result

    def _validate_required_fields(
        self,
        txn: CanonicalTransaction,
        result: ValidationResult,
        row_number: Optional[int],
        trace: Optional[str],
    ) -> None:
        """Check that all required fields are present and non-empty.

        Required fields: id (non-empty string), amount (present),
        currency (non-empty string), status (present).
        """
        # Validate id — must be non-empty string
        if txn.id is None or txn.id.strip() == "":
            result.errors.append(ValidationError(
                field="id",
                reason="required field 'id' is empty or missing",
                row=row_number,
                trace=trace,
            ))

        # Validate currency — must be non-empty string
        if txn.currency is None or txn.currency.strip() == "":
            result.errors.append(ValidationError(
                field="currency",
                reason="required field 'currency' is empty or missing",
                row=row_number,
                trace=trace,
            ))

    def _validate_decimal(
        self,
        txn: CanonicalTransaction,
        result: ValidationResult,
        row_number: Optional[int],
        trace: Optional[str],
    ) -> None:
        """Validate amount business rules.

        - Amount must be non-negative (zero is valid for refunds/zero-value txns).
        - Type correctness already enforced by CanonicalTransaction pydantic model.
        """
        if txn.amount < 0:
            result.errors.append(ValidationError(
                field="amount",
                reason=f"amount must be non-negative, got {txn.amount}",
                row=row_number,
                trace=trace,
            ))

    def _validate_date(
        self,
        txn: CanonicalTransaction,
        result: ValidationResult,
        row_number: Optional[int],
        trace: Optional[str],
    ) -> None:
        """Validate transDate type integrity.

        - transDate is Optional[datetime] — if None, skip (it's optional).
        - If present, confirm it's a datetime instance (defensive type check).
        """
        if txn.transDate is not None:
            if not isinstance(txn.transDate, datetime):
                result.errors.append(ValidationError(
                    field="transDate",
                    reason="transDate must be a datetime object",
                    row=row_number,
                    trace=trace,
                ))
