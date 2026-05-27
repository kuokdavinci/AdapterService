"""Excel streaming reader using openpyxl in read-only mode."""

from collections.abc import Iterator
from pathlib import Path
from typing import Self

from openpyxl import load_workbook
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

VALID_EXTENSIONS = {".xlsx", ".xlsm"}


class ExcelStreamReader:
    """Memory-efficient Excel file reader using openpyxl read-only mode.

    Opens Excel files in read-only mode for constant memory usage regardless
    of file size. Supports context manager protocol for automatic resource cleanup.
    """

    def __init__(
        self,
        file_path: str | Path,
        *,
        sheet_name: str | None = None,
        sheet_index: int | None = None,
        start_row: int = 1,
    ) -> None:
        """Initialize the reader with a file path.

        Args:
            file_path: Path to the Excel file (.xlsx or .xlsm).
            sheet_name: Select sheet by name (mutually exclusive with sheet_index).
            sheet_index: Select sheet by 0-based index (mutually exclusive with sheet_name).
            start_row: 1-based row number to start reading from (default 1 = first row).

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
        self._worksheet: Worksheet | None = None
        self._sheet_name: str | None = sheet_name
        self._sheet_index: int | None = sheet_index
        self._start_row: int = start_row

    def __enter__(self) -> Self:
        """Load the workbook in read-only mode and select the worksheet.

        Returns:
            self for use within the context manager.
        """
        self._workbook = load_workbook(
            filename=str(self._file_path), read_only=True
        )
        self._select_sheet()
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

    def _select_sheet(self) -> None:
        """Select the worksheet based on sheet_name, sheet_index, or default.

        Raises:
            KeyError: If sheet_name is provided but not found.
            IndexError: If sheet_index is provided but out of range.
        """
        self._require_workbook()
        if self._sheet_name is not None:
            if self._sheet_name not in self._workbook.sheetnames:  # type: ignore[union-attr]
                raise KeyError(f"Sheet '{self._sheet_name}' not found")
            self._worksheet = self._workbook[self._sheet_name]  # type: ignore[index]
        elif self._sheet_index is not None:
            try:
                self._worksheet = self._workbook.worksheets[self._sheet_index]  # type: ignore[union-attr]
            except IndexError:
                raise IndexError(
                    f"Sheet index {self._sheet_index} out of range "
                    f"(workbook has {len(self._workbook.worksheets)} sheets)"  # type: ignore[arg-type]
                )
        else:
            self._worksheet = self._workbook.active  # type: ignore[assignment]

    def iter_rows(self) -> Iterator[tuple]:
        """Iterate over rows in the selected worksheet starting from start_row.

        Yields:
            Tuples of cell values (str, int, float, datetime, None, etc.).
            Empty cells yield None.

        Raises:
            RuntimeError: If called outside a context manager block.
        """
        self._require_workbook()
        for row in self._worksheet.iter_rows(  # type: ignore[union-attr]
            min_row=self._start_row, values_only=True
        ):
            yield row
