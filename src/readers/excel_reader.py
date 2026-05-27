"""Excel streaming reader using openpyxl in read-only mode."""

from pathlib import Path
from typing import Self

from openpyxl import load_workbook
from openpyxl.workbook import Workbook

VALID_EXTENSIONS = {".xlsx", ".xlsm"}


class ExcelStreamReader:
    """Memory-efficient Excel file reader using openpyxl read-only mode.

    Opens Excel files in read-only mode for constant memory usage regardless
    of file size. Supports context manager protocol for automatic resource cleanup.
    """

    def __init__(self, file_path: str | Path) -> None:
        """Initialize the reader with a file path.

        Args:
            file_path: Path to the Excel file (.xlsx or .xlsm).

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file extension is not .xlsx or .xlsm.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if path.suffix.lower() not in VALID_EXTENSIONS:
            raise ValueError(
                f"Unsupported file extension '{path.suffix}'. "
                f"Must be one of: {', '.join(sorted(VALID_EXTENSIONS))}"
            )
        self._file_path: Path = path
        self._workbook: Workbook | None = None

    def __enter__(self) -> Self:
        """Load the workbook in read-only mode.

        Returns:
            self for use within the context manager.
        """
        self._workbook = load_workbook(
            filename=str(self._file_path), read_only=True
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Close the workbook, even if an exception occurred.

        Returns:
            False — does not suppress exceptions.
        """
        if self._workbook is not None:
            self._workbook.close()
            self._workbook = None
        return False

    def _require_workbook(self) -> None:
        """Raise RuntimeError if workbook is not loaded.

        Raises:
            RuntimeError: If called outside a context manager block.
        """
        if self._workbook is None:
            raise RuntimeError("Reader must be used as context manager")

    def get_sheet_names(self) -> list[str]:
        """Return the list of sheet names in the workbook.

        Returns:
            List of sheet name strings.

        Raises:
            RuntimeError: If called outside a context manager block.
        """
        self._require_workbook()
        return self._workbook.sheetnames  # type: ignore[union-attr]
