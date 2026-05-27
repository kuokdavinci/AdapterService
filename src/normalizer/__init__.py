"""Normalization package for the reconciliation ingestion platform.

Exports:
    TransactionNormalizer: Core normalization engine.
    NormalizationResult: Dataclass holding normalized data and errors.
"""

from src.normalizer.normalizer import NormalizationResult, TransactionNormalizer

__all__ = ["TransactionNormalizer", "NormalizationResult"]
