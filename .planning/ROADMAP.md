# Reconciliation Ingestion Platform - Roadmap

## Requirements

**Phase 1:** FOUND-01, FOUND-02, FOUND-03
**Phase 2:** READER-01, READER-02
**Phase 3:** CONFIG-01, CONFIG-02
**Phase 4:** NORM-01, NORM-02
**Phase 5:** VALID-01, VALID-02
**Phase 6:** PERSIST-01, PERSIST-02
**Phase 7:** LOG-01, LOG-02

---

## Phase 1: Foundation

**Goal:** Project skeleton, database models, core type definitions, and configuration structure

**Requirements:**
- FOUND-01: Project structure with Python package layout, dependencies (openpyxl, pydantic, motor/pymongo, python-decouple)
- FOUND-02: MongoDB models for reconciliation_file, reconciliation_mapping_config, data_container
- FOUND-03: Core canonical transaction types and constants

**Plans:** 2 plans

Plans:
- [x] 01-01-PLAN.md — Project structure, core types, enums, constants, configuration
- [x] 01-02-PLAN.md — MongoDB models, repositories, indexes

---

## Phase 2: File Reader

**Goal:** Excel file reader with streaming support, sheet selection, and row filtering

**Requirements:**
- READER-01: Stream Excel rows efficiently using openpyxl read-only mode
- READER-02: Support configurable sheet selection, skip empty/summary rows

**Plans:** 2 plans

Plans:
- [x] 02-01-PLAN.md — Core Excel streaming reader with openpyxl read-only mode, sheet selection, start_row
- [x] 02-02-PLAN.md — Row filtering (empty/summary), MappingConfig integration, comprehensive tests

---

## Phase 3: Mapping Configuration

**Goal:** Dynamic mapping configuration engine that loads and interprets partner-specific parsing rules

**Requirements:**
- CONFIG-01: Mapping config loader from MongoDB (field mappings, transformations, status mappings, constants)
- CONFIG-02: Config versioning and caching

**Plans:** 2 plans

Plans:
- [x] 03-01-PLAN.md — ConfigCache (TTL in-memory) and ConfigValidator (field mapping integrity checks)
- [x] 03-02-PLAN.md — ConfigLoader service with repository, cache, validator integration + full test suite

---

## Phase 4: Normalization

**Goal:** Dynamic mapper that converts partner-specific fields into canonical transaction model

**Requirements:**
- NORM-01: Dynamic field mapping engine (column → canonical field, type conversion, constant values)
- NORM-02: Status normalization (partner-specific status → canonical SUCCESS/FAILED/etc.)

**Plans:** 2 plans

Plans:
- [ ] 04-01-PLAN.md — Core TransactionNormalizer with STRING/DECIMAL/DATE/CONSTANT type conversion and error collection
- [ ] 04-02-PLAN.md — MAPPING type status normalization, CanonicalTransaction builder, comprehensive tests

---

## Phase 5: Validation

**Goal:** Validation layer for normalized transactions

**Requirements:**
- VALID-01: Required field validation, decimal validation, date validation, status validation
- VALID-02: Duplicate detection (identify + reconciliationDate + trace, fileHash)

**Plans:** 0 plans

---

## Phase 6: Persistence & Ingestion Pipeline

**Goal:** Database persistence layer and full ingestion pipeline orchestration

**Requirements:**
- PERSIST-01: Save normalized transactions to data_container, update reconciliation_file statistics
- PERSIST-02: Full ingestion pipeline orchestration (file → read → map → normalize → validate → persist)

**Plans:** 0 plans

---

## Phase 7: Logging & Tracking

**Goal:** Structured logging, file processing lifecycle tracking, and processing statistics

**Requirements:**
- LOG-01: Structured JSON logging (fileId, row, trace, status, reason)
- LOG-02: File processing lifecycle tracking (PROCESSING → COMPLETED/FAILED), statistics (total/success/failed rows)

**Plans:** 0 plans
