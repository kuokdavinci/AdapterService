"""Core enums for processing status, transaction status, and file types."""

from enum import StrEnum


class ProcessingStatus(StrEnum):
    """Status of a file processing job."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TransactionStatus(StrEnum):
    """Status of an individual transaction."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    REVERSED = "REVERSED"


class FileType(StrEnum):
    """Type of ingestion file."""

    SETTLEMENT = "SETTLEMENT"
    RECONCILIATION = "RECONCILIATION"
