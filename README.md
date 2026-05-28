# Reconciliation Ingestion Platform

A configurable reconciliation ingestion platform that reads partner settlement reports, normalizes heterogeneous transaction data into a canonical model, and persists them into MongoDB — all driven by dynamic configuration with zero hardcoded parsing logic.

## Quick Start

```bash
# Install dependencies
uv sync --all-extras

# Configure environment
cp .env.example .env

# Run tests
uv run python -m pytest -v

# Apply MongoDB indexes
python -c "import asyncio; from src.models.indexes import apply_indexes; from motor.motor_asyncio import AsyncIOMotorClient; from src.config.settings import settings; client = AsyncIOMotorClient(settings.mongodb_url); asyncio.run(apply_indexes(client[settings.db_name]))"
```

## Architecture

```
Partner Excel File
       ↓
┌─────────────────────────┐
│  ExcelStreamReader      │  openpyxl read-only, constant memory
│  (skip empty/summary)   │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  ConfigLoader           │  TTL cache, validation, version resolution
│  (MappingConfig)        │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  TransactionNormalizer  │  STRING/DECIMAL/DATE/MAPPING/CONSTANT
│  (dynamic mapping)      │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  Validator              │  Required fields, decimal, date, status
│  (duplicate detection)  │  identify + reconciliationDate + trace
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  IngestionPipeline      │  Orchestration, batch insert, logging
│  (process_file)         │  SHA256 dedup, stats tracking
└───────────┬─────────────┘
            ↓
     ┌──────────────┐
     │  MongoDB     │  reconciliation_file, mapping_config, data_container
     └──────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.14 |
| Database | MongoDB + motor (async driver) |
| Excel | openpyxl (read-only/streaming mode) |
| Validation | pydantic v2 |
| Config | pydantic-settings (env prefix `APP_`) |
| Decimal | `Decimal` (never float for money) |
| Logging | Python stdlib `logging` with JSON formatter |
| Testing | pytest + pytest-asyncio |

## Key Features

- **Zero hardcoded parsers** — all column mapping, transformations, and status normalization are defined in MongoDB `MappingConfig` documents
- **Memory-efficient** — openpyxl read-only mode streams rows, constant memory regardless of file size
- **Duplicate prevention** — SHA256 file hash + composite key (identify + reconciliationDate + trace)
- **Batch insertion** — configurable batch size (default 100) for efficient MongoDB writes
- **Structured logging** — JSON output with 5 event types (FILE_STARTED, FILE_COMPLETED, FILE_FAILED, ROW_SUCCESS, ROW_FAILED)
- **Audit trail** — every record includes createdBy, createdDate, lastModifiedBy, lastModifiedDate

## Project Structure

```
src/
├── core/           # Canonical types, enums, constants
├── config/         # Settings, ConfigCache, ConfigValidator, ConfigLoader
├── readers/        # ExcelStreamReader (openpyxl read-only)
├── normalizer/     # TransactionNormalizer (dynamic field mapping)
├── validators/     # Validator (business rules + duplicate detection)
├── pipeline/       # IngestionPipeline (full orchestration)
├── logging/        # StructuredLogger (JSON/text formatters)
└── models/         # MongoDB models, repositories, indexes
tests/              # 318 tests across all modules
```

## MongoDB Collections

| Collection | Purpose | Key Indexes |
|------------|---------|-------------|
| `reconciliation_file` | Track uploaded files, processing stats | `fileHash` (unique), `partner + reconciliationDate` |
| `reconciliation_mapping_config` | Dynamic parsing configuration per partner | `partner + workflowType + fileType` |
| `data_container` | Canonical normalized transactions | `partnerData.trace`, `identify + reconciliationDate`, `operationStatus` |

## Configuration

All settings use `APP_` prefix environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `APP_DB_NAME` | `reconciliation` | Database name |
| `APP_LOG_LEVEL` | `INFO` | Log level (DEBUG/INFO/WARNING/ERROR) |
| `APP_LOG_FORMAT` | `json` | Log format (json/text) |
| `APP_APP_NAME` | `reconciliation-ingestion` | Application name |

## Onboarding a New Partner

1. Insert a `MappingConfig` document into `reconciliation_mapping_config` with field mappings
2. No code changes needed — the platform reads config dynamically

Example MappingConfig:
```json
{
  "partner": "MOMO",
  "workflowType": "UPC",
  "fileType": "SETTLEMENT",
  "sheetName": "Sheet1",
  "startRow": 2,
  "fieldMappings": [
    { "path": "id", "column": "A", "type": "STRING", "required": true },
    { "path": "amount", "column": "D", "type": "DECIMAL" },
    { "path": "currency", "constant": "VND", "type": "CONSTANT" },
    { "path": "status", "column": "Q", "type": "MAPPING", "mapping": { "Thành công": "SUCCESS", "others": "FAILED" } }
  ]
}
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Decimal, never float | Prevent floating-point precision errors in financial calculations |
| partnerData as nested object | Easier MongoDB querying, indexing, aggregation |
| camelCase aliases in MongoDB | Matches requirement.md schema, industry standard |
| Error collection (not fail-fast) | Full audit trail — every row error is recorded |
| openpyxl read-only mode | Constant memory for large files (100K+ rows) |

## License

Private — internal use only.
