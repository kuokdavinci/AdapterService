import tempfile
import pytest
from pathlib import Path
from src.core.enums import FileType
from src.models.mapping_config import MappingConfig
from src.readers.csv_reader import CSVStreamReader

@pytest.fixture
def temp_csv_file():
    """Creates a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write("Header1,Header2,Header3\n")
        f.write("val1,val2,val3\n")
        f.write("val4,val5,val6\n")
        f.write(",,\n")  # Empty row
        f.write("val7,val8,val9\n")
        f.write("Total,,1000\n")  # Summary row
        file_path = f.name
    yield file_path
    Path(file_path).unlink()

def test_csv_reader_basic(temp_csv_file):
    """Happy path reading of CSV file using context manager."""
    with CSVStreamReader(temp_csv_file, start_row=2) as reader:
        rows = list(reader.iter_rows())
    
    assert len(rows) == 3
    assert rows[0] == ("val1", "val2", "val3")
    assert rows[1] == ("val4", "val5", "val6")
    # Empty row and Total row are skipped by default
    assert rows[2] == ("val7", "val8", "val9")

def test_csv_reader_custom_delimiter():
    """Read CSV with semicolon delimiter."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write("colA;colB\n")
        f.write("valA;valB\n")
        file_path = f.name

    try:
        with CSVStreamReader(file_path, start_row=2, delimiter=";") as reader:
            rows = list(reader.iter_rows())
        assert len(rows) == 1
        assert rows[0] == ("valA", "valB")
    finally:
        Path(file_path).unlink()

def test_csv_reader_start_row(temp_csv_file):
    """Skip to start_row when reading."""
    with CSVStreamReader(temp_csv_file, start_row=3) as reader:
        rows = list(reader.iter_rows())
    assert len(rows) == 2
    assert rows[0] == ("val4", "val5", "val6")

def test_csv_reader_skip_empty_rows(temp_csv_file):
    """Disable skipping empty rows."""
    with CSVStreamReader(temp_csv_file, start_row=2, skip_empty_rows=False) as reader:
        rows = list(reader.iter_rows())
    # Should include the empty row as (None, None, None) or ("", "", "")
    assert len(rows) == 4
    assert rows[2] == ("", "", "") or rows[2] == (None, None, None)

def test_csv_reader_skip_patterns(temp_csv_file):
    """Disable summary row skipping or customize skip patterns."""
    with CSVStreamReader(temp_csv_file, start_row=2, skip_patterns=[]) as reader:
        rows = list(reader.iter_rows())
    assert len(rows) == 4  # Includes the total row
    assert rows[3] == ("Total", "", "1000")

def test_csv_reader_from_mapping_config(temp_csv_file):
    """Instantiate from MappingConfig object."""
    config = MappingConfig(
        partner="TEST",
        workflow_type="UPC",
        file_type=FileType.SETTLEMENT,
        sheet_name="ignored",
        start_row=2,
        field_mappings=[]
    )
    with CSVStreamReader.from_mapping_config(temp_csv_file, config) as reader:
        rows = list(reader.iter_rows())
    assert len(rows) == 3
    assert rows[0] == ("val1", "val2", "val3")
