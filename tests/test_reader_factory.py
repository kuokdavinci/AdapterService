import pytest
from pathlib import Path
from src.core.enums import FileType
from src.models.mapping_config import MappingConfig
from src.readers import create_reader, ExcelStreamReader, CSVStreamReader

@pytest.fixture
def dummy_mapping_config():
    return MappingConfig(
        partner="TEST",
        workflow_type="UPC",
        file_type=FileType.SETTLEMENT,
        sheet_name="Sheet1",
        start_row=2,
        field_mappings=[]
    )

def test_create_reader_excel(dummy_mapping_config):
    # We just need to check the returned class type without actually opening the file (since it raises FileNotFoundError)
    # But wait, create_reader actually constructs the object, and constructors check if the file exists.
    # So we must pass a path to a file that exists or mock it, or create a temp file.
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        xlsx_path = f.name
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        csv_path = f.name
        
    try:
        reader = create_reader(xlsx_path, dummy_mapping_config)
        assert isinstance(reader, ExcelStreamReader)
        
        reader = create_reader(csv_path, dummy_mapping_config)
        assert isinstance(reader, CSVStreamReader)
    finally:
        Path(xlsx_path).unlink()
        Path(csv_path).unlink()

def test_create_reader_unsupported(dummy_mapping_config):
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        json_path = f.name
        
    try:
        with pytest.raises(ValueError, match="Unsupported file format"):
            create_reader(json_path, dummy_mapping_config)
    finally:
        Path(json_path).unlink()
