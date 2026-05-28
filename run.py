import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
import paramiko

from src.config.settings import settings
from src.config.loader import ConfigLoader
from src.config.cache import ConfigCache
from src.config.validator import ConfigValidator
from src.core.enums import FileType
from src.models.mapping_config import MappingConfigRepository
from src.pipeline.ingestion_pipeline import IngestionPipeline

async def run_pipeline():
    print("=== Reconciliation Ingestion Pipeline ===")
    
    # 1. SFTP Connection and File Download
    sftp_host = os.getenv("SFTP_HOST", "localhost")
    sftp_port = int(os.getenv("SFTP_PORT", "2222"))
    sftp_user = os.getenv("SFTP_USER", "foo")
    sftp_pass = os.getenv("SFTP_PASS", "pass")
    
    # Target file details
    partner = "MOMO"
    workflow_type = "UPC"
    file_type = FileType.SETTLEMENT
    reconciliation_date = datetime(2024, 7, 7, tzinfo=timezone.utc)
    
    # We look for the sample file
    remote_filename = "m4becomvsp_07072024_combine.xlsx"
    remote_path = f"/upload/{remote_filename}"
    
    local_dir = Path("./tmp_downloads")
    local_dir.mkdir(exist_ok=True)
    local_path = local_dir / remote_filename
    
    print(f"Connecting to SFTP {sftp_user}@{sftp_host}:{sftp_port}...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(sftp_host, port=sftp_port, username=sftp_user, password=sftp_pass, timeout=10)
        
        sftp = ssh.open_sftp()
        print(f"Downloading {remote_path} from SFTP...")
        sftp.get(remote_path, str(local_path))
        sftp.close()
        ssh.close()
        print(f"File downloaded successfully to {local_path}")
    except Exception as e:
        print(f"SFTP connection/download failed: {e}")
        # Fallback to checking sftp_data directory locally
        fallback_path = Path("./sftp_data") / remote_filename
        if fallback_path.exists():
            print(f"Using local sftp_data fallback: {fallback_path}")
            local_path = fallback_path
        else:
            print("Error: Could not retrieve file from SFTP or local sftp_data folder.")
            return

    # 2. Database Connection and Pipeline Orchestration
    print(f"Connecting to MongoDB at {settings.mongodb_url}...")
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.db_name]
    
    # Clean up previous records for a fresh test run
    print("Cleaning up any existing records for MOMO on 2024-07-07...")
    await db["reconciliation_file"].delete_many({"partner": partner, "reconciliationDate": reconciliation_date})
    await db["data_container"].delete_many({"identify": partner, "reconciliationDate": reconciliation_date})
    
    config_repo = MappingConfigRepository(db)
    config_cache = ConfigCache()
    config_validator = ConfigValidator()
    config_loader = ConfigLoader(config_repo, config_cache, config_validator)
    
    pipeline = IngestionPipeline(db=db, config_loader=config_loader)
    
    print("Processing file through ingestion pipeline...")
    result = await pipeline.process_file(
        file_path=str(local_path),
        partner=partner,
        workflow_type=workflow_type,
        file_type=file_type,
        reconciliation_date=reconciliation_date,
        config_version="v_template"
    )
    
    # 3. Print Results
    print("\n=== Pipeline Processing Summary ===")
    print(f"Status: {result.file_record.processing_status}")
    print(f"Total Rows: {result.stats.total_rows}")
    print(f"Success Rows: {result.stats.success_rows}")
    print(f"Failed Rows: {result.stats.failed_rows}")
    
    if result.errors:
        print(f"Errors ({len(result.errors)}):")
        for err in result.errors[:5]:
            print(f"  - Row {err.get('row', 'N/A')}: {err.get('field')} -> {err.get('reason')}")
            
    # Count database documents
    saved_count = await db["data_container"].count_documents({"identify": partner})
    print(f"Verified documents in MongoDB (data_container): {saved_count}")
    
    # Cleanup temp download file
    if local_path.exists() and "tmp_downloads" in str(local_path):
        local_path.unlink()
        local_dir.rmdir()
        print("Cleaned up temporary download files.")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
