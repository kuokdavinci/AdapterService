"""Excel and CSV streaming reader package."""

from pathlib import Path
from src.readers.excel_reader import ExcelStreamReader
from src.readers.csv_reader import CSVStreamReader
from src.models.mapping_config import MappingConfig

def create_reader(file_path: str | Path, config: MappingConfig) -> ExcelStreamReader | CSVStreamReader:
    """Factory function to dynamically create a reader based on the file extension.

    Args:
        file_path: Path to the file.
        config: MappingConfig containing reading parameters.

    Returns:
        Configured ExcelStreamReader or CSVStreamReader instance.

    Raises:
        ValueError: If the file extension is not supported.
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".csv":
        return CSVStreamReader.from_mapping_config(file_path, config)
    elif ext in {".xlsx", ".xlsm"}:
        return ExcelStreamReader.from_mapping_config(file_path, config)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

__all__ = ["ExcelStreamReader", "CSVStreamReader", "create_reader"]
