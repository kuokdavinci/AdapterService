"""Pipeline package — ingestion orchestration for reconciliation files.

Exports:
    IngestionPipeline: Main pipeline class with async process_file() method.
    IngestionResult: Dataclass holding processing results.
"""

from src.pipeline.ingestion_pipeline import IngestionPipeline, IngestionResult

__all__ = ["IngestionPipeline", "IngestionResult"]
