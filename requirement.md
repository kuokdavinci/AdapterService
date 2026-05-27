# Reconciliation Ingestion Platform - Project Summary

## 1. Project Overview

### Objective

Build a configurable reconciliation ingestion platform capable of:

* Reading settlement/reconciliation reports from multiple partners.
* Parsing partner files dynamically using configuration.
* Normalizing heterogeneous transaction data into a canonical internal structure.
* Persisting normalized transactions into the database.
* Supporting future reconciliation workflows.

---

# 2. Current Scope

The current phase only includes:

* File ingestion
* Dynamic mapping
* Data normalization
* Validation
* Database persistence
* Logging and tracking

Not included yet:

* Reconciliation engine
* Connector integration
* Automated compensation
* Settlement comparison
* Repair workflow
* Retry orchestration

---

# 3. Problem Statement

Different partners provide settlement reports with:

* Different column names
* Different sheet layouts
* Different date formats
* Different status formats
* Different transaction structures

The system must:

* Avoid hardcoded parsers
* Support onboarding new partners quickly
* Normalize all partner data into a unified transaction model
* Preserve auditability and replay capability

---

# 4. High-Level Architecture

```text
Partner Settlement File
↓
File Reader
↓
Mapping Config Loader
↓
Dynamic Mapper
↓
Normalizer
↓
Validator
↓
Canonical Transaction Model
↓
Database Persistence
```

---

# 5. Core System Components

## 5.1 File Reader

Responsibilities:

* Read Excel files
* Stream rows efficiently
* Skip empty rows
* Skip summary/footer rows
* Support configurable sheet selection

Suggested libraries:

* Python: openpyxl
* Java: Apache POI

---

## 5.2 Mapping Configuration Engine

Responsibilities:

* Define column-to-field mapping
* Define transformation rules
* Define status mapping rules
* Define constant values
* Define validation rules

Purpose:

* Avoid hardcoded parsing logic
* Support multiple partner formats dynamically

---

## 5.3 Normalization Layer

Responsibilities:

Convert partner-specific fields into canonical fields.

Examples:

| Partner Field | Canonical Field |
| ------------- | --------------- |
| msTotalAmount | amount          |
| paymentAmount | amount          |
| settleAmt     | amount          |

---

## 5.4 Validation Layer

Responsibilities:

* Validate required fields
* Validate decimal amount
* Validate date formats
* Validate transaction identifiers
* Validate status mapping

Validation output:

```json
{
  "field": "amount",
  "reason": "INVALID_DECIMAL"
}
```

---

## 5.5 Persistence Layer

Responsibilities:

* Save normalized transactions
* Save ingestion metadata
* Save processing statistics
* Preserve audit history

---

# 6. Database Design

## 6.1 reconciliation_file

Purpose:

Track uploaded/imported files.

### Structure

```json
{
  "_id": "uuid",
  "partner": "MOMO",
  "fileName": "m4becomvsp_07072024_combine.xlsx",
  "fileHash": "sha256",
  "fileType": "SETTLEMENT",
  "reconciliationDate": "2024-07-07",
  "processingStatus": "PROCESSING",
  "totalRows": 1000,
  "successRows": 990,
  "failedRows": 10,
  "configVersion": "v1",
  "uploadedAt": "ISODate",
  "createdBy": "system",
  "createdAt": "ISODate"
}
```

### Purpose of Important Fields

| Field              | Purpose                     |
| ------------------ | --------------------------- |
| fileHash           | Duplicate file detection    |
| processingStatus   | Track ingestion lifecycle   |
| configVersion      | Trace parsing configuration |
| reconciliationDate | Settlement date reference   |

---

# 6.2 reconciliation_mapping_config

Purpose:

Dynamic parsing configuration.

### Structure

```json
{
  "_id": "uuid",
  "partner": "MOMO",
  "workflowType": "UPC",
  "fileType": "SETTLEMENT",
  "sheetName": "Sheet1",
  "startRow": 2,
  "fieldMappings": [
    {
      "path": "_id",
      "column": "A",
      "sourceField": "msTransId",
      "type": "STRING",
      "required": true
    },
    {
      "path": "trace",
      "column": "J",
      "sourceField": "msMaHDon",
      "type": "STRING"
    },
    {
      "path": "amount",
      "column": "D",
      "type": "DECIMAL"
    },
    {
      "path": "currency",
      "constant": "VND"
    },
    {
      "path": "status",
      "column": "Q",
      "mapping": {
        "Thành công": "SUCCESS",
        "others": "FAILED"
      }
    }
  ],
  "createdAt": "ISODate"
}
```

### Key Design Principles

* Generic configuration structure
* No hardcoded partner logic
* Nested field mapping support
* Transformation support
* Status normalization support

---

# 6.3 data_container

Purpose:

Canonical normalized transaction storage.

### Structure

```json
{
  "_id": "uuid",
  "requestId": "uuid",
  "identify": "MOMO",
  "workflowType": "UPC",
  "reconciliationDate": "2024-07-07",
  "operationStatus": "IN_PROGRESS",
  "reconciliationStatus": "",
  "connectorData": "",
  "extraData": "",
  "sourceFileId": "reconciliation_file_id",
  "partnerData": {
    "_id": "61838642196",
    "trace": "2407055711887385978413624",
    "status": "SUCCESS",
    "amount": "Decimal128(259200)",
    "currency": "VND",
    "transDate": "ISODate",
    "extra": {
      "service": "PAYMENT",
      "portal": "PaymentGateway",
      "provider": "MOMO",
      "method": "MOMO",
      "vspTransId": "2407055711887385978413624",
      "merchantSettleDate": "ISODate",
      "providerSettleDate": "ISODate"
    }
  },
  "createdBy": "system",
  "createdDate": "ISODate",
  "lastModifiedBy": "system",
  "lastModifiedDate": "ISODate"
}
```

---

# 7. Canonical Transaction Model

Purpose:

Normalize all partner transaction structures into a unified internal format.

### Canonical Fields

| Field     | Description                      |
| --------- | -------------------------------- |
| _id       | Partner transaction identifier   |
| trace     | Transaction trace/reference      |
| amount    | Transaction amount               |
| currency  | Currency code                    |
| status    | Normalized transaction status    |
| transDate | Transaction completion time      |
| extra     | Partner-specific additional data |

---

# 8. Important Technical Decisions

## 8.1 Decimal Handling

Requirement:

* Never use float/double for money.

Recommended:

* Python: Decimal
* Java: BigDecimal
* MongoDB: Decimal128

Reason:

Avoid floating-point precision issues.

---

## 8.2 Dynamic Mapping

Requirement:

* No hardcoded Excel columns.

Reason:

Each partner may:

* Change column order
* Change sheet layout
* Add/remove fields

---

## 8.3 partnerData as Object

Recommended:

Store partnerData as nested object instead of JSON string.

Reason:

* Easier querying
* Easier indexing
* Easier reconciliation
* Better aggregation support

---

# 9. Validation Rules

## Required Validation

| Validation           | Description                   |
| -------------------- | ----------------------------- |
| Required fields      | Ensure mandatory fields exist |
| Decimal validation   | Ensure valid monetary amount  |
| Date validation      | Ensure valid transaction date |
| Status normalization | Ensure valid canonical status |
| Duplicate detection  | Prevent duplicated ingestion  |

---

# 10. Duplicate Prevention

Important because:

* Files may be re-uploaded
* Jobs may retry
* Cron jobs may rerun

Recommended unique keys:

```text
identify + reconciliationDate + trace
```

or

```text
fileHash
```

---

# 11. Index Recommendation

## reconciliation_file

```text
fileHash UNIQUE
partner + reconciliationDate
```

## data_container

```text
partnerData.trace
identify + reconciliationDate
operationStatus
partnerData.status
```

---

# 12. Logging Requirements

System should log:

* Total rows processed
* Successful rows
* Failed rows
* Parsing failures
* Validation failures
* File processing lifecycle

### Structured Log Example

```json
{
  "fileId": "uuid",
  "row": 142,
  "trace": "2407055711887385978413624",
  "status": "FAILED_PARSE",
  "reason": "INVALID_DATE"
}
```

---

# 13. Suggested Processing Flow

```text
Upload File
↓
Create reconciliation_file record
↓
Load mapping config
↓
Read rows
↓
Normalize transaction
↓
Validate transaction
↓
Persist data_container
↓
Update processing statistics
↓
Mark file completed
```

---

# 14. Scalability Considerations

## Recommended Practices

* Stream Excel rows instead of loading entire file into memory
* Keep ingestion idempotent
* Preserve auditability
* Version configuration changes
* Separate raw ingestion from reconciliation workflow

---

# 15. Future Extensions

Planned future capabilities:

* Reconciliation engine
* Connector integration
* Automated discrepancy detection
* Compensation workflow
* Retry orchestration
* Settlement comparison
* Repair pipeline
* Dashboard/reporting
* Distributed job execution

---

# 16. Recommended Technology Stack

## Python Stack

| Purpose      | Recommendation       |
| ------------ | -------------------- |
| Excel Reader | openpyxl             |
| Validation   | pydantic             |
| Decimal      | Decimal              |
| Database     | MongoDB              |
| Scheduler    | APScheduler          |
| Logging      | Structured JSON Logs |

## Java Stack

| Purpose      | Recommendation            |
| ------------ | ------------------------- |
| Excel Reader | Apache POI                |
| Validation   | Hibernate Validator       |
| Decimal      | BigDecimal                |
| Database     | MongoDB/Postgres          |
| Scheduler    | Spring Scheduler / Quartz |
| Logging      | Logback JSON              |

---

# 17. Architectural Mindset

This project is not just:

```text
Excel Import
```

It is the foundation of a:

```text
Partner Settlement Ingestion Platform
```

Core engineering goals:

* Dynamic configuration
* Canonical normalization
* Auditability
* Replay safety
* Scalability
* Future reconciliation support
* Financial correctness
