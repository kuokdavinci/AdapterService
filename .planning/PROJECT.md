# Reconciliation Ingestion Platform - Project

## Overview
A configurable reconciliation ingestion platform that reads settlement/reconciliation reports from multiple partners, parses files dynamically using configuration, normalizes heterogeneous transaction data into a canonical internal structure, and persists normalized transactions into MongoDB.

## Tech Stack
- **Language:** Python 3.14
- **Excel Reader:** openpyxl (streaming)
- **Validation:** pydantic
- **Decimal:** Python Decimal (never float/double for money)
- **Database:** MongoDB with Decimal128
- **Logging:** Structured JSON logs

## Architecture
```
Partner Settlement File → File Reader → Mapping Config Loader → Dynamic Mapper → Normalizer → Validator → Canonical Transaction Model → Database Persistence
```

## Core Principles
- Dynamic configuration (no hardcoded parsers)
- Canonical normalization
- Auditability and replay safety
- Financial correctness (Decimal128 for money)
- Idempotent ingestion
- Scalability (stream rows, don't load entire file)

## Current Scope (This Milestone)
- File ingestion (Excel)
- Dynamic mapping configuration
- Data normalization
- Validation layer
- Database persistence
- Logging and tracking

## Out of Scope (Future)
- Reconciliation engine
- Connector integration
- Automated compensation
- Settlement comparison
- Repair workflow
- Retry orchestration
