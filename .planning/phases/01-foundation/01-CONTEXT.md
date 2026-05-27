# Phase 1: Foundation - Context

## User Decisions

### Locked Decisions
- **D-01:** Python 3.14 as primary language
- **D-02:** MongoDB as database with motor async driver
- **D-03:** openpyxl for Excel reading (read-only/streaming mode)
- **D-04:** pydantic for validation and data modeling
- **D-05:** Python Decimal for monetary values (never float/double)
- **D-06:** Structured JSON logging
- **D-07:** python-decouple for environment configuration

### OpenCode's Discretion
- Package structure layout (standard Python package)
- Async vs sync approach (async preferred for MongoDB with motor)
- Testing framework choice (pytest standard)

## Requirements (from ROADMAP)
- FOUND-01: Project structure with Python package layout, dependencies
- FOUND-02: MongoDB models for reconciliation_file, reconciliation_mapping_config, data_container
- FOUND-03: Core canonical transaction types and constants

## Database Schema (from requirement.md)

### reconciliation_file
- _id: UUID
- partner: string (e.g., "MOMO")
- fileName: string
- fileHash: string (SHA256, UNIQUE)
- fileType: string (e.g., "SETTLEMENT")
- reconciliationDate: date
- processingStatus: enum (PENDING, PROCESSING, COMPLETED, FAILED)
- totalRows: int
- successRows: int
- failedRows: int
- configVersion: string
- uploadedAt: datetime
- createdBy: string
- createdAt: datetime

### reconciliation_mapping_config
- _id: UUID
- partner: string
- workflowType: string (e.g., "UPC")
- fileType: string
- sheetName: string
- startRow: int
- fieldMappings: array of field mapping objects
- createdAt: datetime

### data_container
- _id: UUID
- requestId: UUID
- identify: string (partner identifier)
- workflowType: string
- reconciliationDate: date
- operationStatus: string
- reconciliationStatus: string
- connectorData: string
- extraData: string
- sourceFileId: reference to reconciliation_file
- partnerData: nested object (not JSON string)
  - _id: string
  - trace: string
  - status: string
  - amount: Decimal128
  - currency: string
  - transDate: datetime
  - extra: object (partner-specific fields)
- createdBy: string
- createdDate: datetime
- lastModifiedBy: string
- lastModifiedDate: datetime

## Canonical Transaction Fields
| Field     | Description                      |
| --------- | -------------------------------- |
| _id       | Partner transaction identifier   |
| trace     | Transaction trace/reference      |
| amount    | Transaction amount (Decimal)     |
| currency  | Currency code                    |
| status    | Normalized transaction status    |
| transDate | Transaction completion time      |
| extra     | Partner-specific additional data |

## Indexes (from requirement.md)
### reconciliation_file
- fileHash: UNIQUE
- partner + reconciliationDate: compound

### data_container
- partnerData.trace
- identify + reconciliationDate: compound
- operationStatus
- partnerData.status
