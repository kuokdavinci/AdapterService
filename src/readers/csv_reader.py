from __future__ import annotations
import csv
from collections.abc import Iterator
from pathlib import Path
from typing import Self, Optional

from src.models.mapping_config import MappingConfig

class CSVStreamReader:
    """Memory-efficient CSV file reader using Python's standard csv module.

    Reads CSV files line-by-line for constant memory usage. Supports context manager
    protocol for automatic file resource cleanup.
    """

    DEFAULT_SKIP_PATTERNS: list[str] = [
        "total",
        "grand total",
        "summary",
        "footer",
        "合计",
        "总计",
        "小计",
    ]

    def __init__(
        self,
        file_path: str | Path,
        *,
        start_row: int = 1,
        skip_empty_rows: bool = True,
        skip_patterns: list[str] | None = None,
        delimiter: str = ",",
        encoding: str = "utf-8",
    ) -> None:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        self._file_path: Path = path
        self._start_row: int = start_row
        self._skip_empty_rows: bool = skip_empty_rows
        self._skip_patterns: list[str] | None = (
            skip_patterns if skip_patterns is not None
            else self.DEFAULT_SKIP_PATTERNS
        )
        self._delimiter: str = delimiter
        self._encoding: str = encoding
        self._file_handle = None
        self._csv_reader = None

    @classmethod
    def from_mapping_config(
        cls, file_path: str | Path, config: MappingConfig
    ) -> CSVStreamReader:
        """Create a CSVStreamReader from a MappingConfig object.

        Uses config.start_row to configure the reader.
        """
        # If there is a delimiter custom config or extension logic in the future, it can be passed here.
        return cls(
            file_path=file_path,
            start_row=config.start_row,
            skip_empty_rows=True,
        )

    def __enter__(self) -> Self:
        self._file_handle = open(self._file_path, mode="r", encoding=self._encoding, newline="")
        self._csv_reader = csv.reader(self._file_handle, delimiter=self._delimiter)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._file_handle is not None:
            self._file_handle.close()
            self._file_handle = None
            self._csv_reader = None
        return False

    def _require_file(self) -> None:
        if self._file_handle is None or self._csv_reader is None:
            raise RuntimeError("Reader must be used as context manager")

    @staticmethod
    def _is_empty_row(row: list[str]) -> bool:
        return all(cell is None or cell == "" for cell in row)

    def _should_skip_row(self, row: list[str]) -> bool:
        if self._skip_empty_rows and self._is_empty_row(row):
            return True

        if self._skip_patterns:
            for cell in row:
                if cell is None:
                    continue
                cell_str = str(cell).lower()
                for pattern in self._skip_patterns:
                    if pattern.lower() in cell_str:
                        return True

        return False

    def iter_rows(self) -> Iterator[tuple[str, ...]]:
        self._require_file()
        
        # Skip rows before start_row (1-based index)
        for current_row_num, row in enumerate(self._csv_reader, start=1):
            if current_row_num < self._start_row:
                continue
            if self._should_skip_row(row):
                continue
            yield tuple(row)
