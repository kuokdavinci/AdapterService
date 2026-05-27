---
phase: 01-foundation
fixed_at: 2026-05-27T16:10:00Z
review_path: .planning/phases/01-foundation/01-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-05-27T16:10:00Z
**Source review:** .planning/phases/01-foundation/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 7
- Fixed: 7
- Skipped: 0

## Fixed Issues

### CR-01: Index `file_hash` should be `fileHash` (reconciliation_file)

**Files modified:** `src/models/indexes.py`
**Commit:** 359b0d7
**Applied fix:** Changed index field from `"file_hash"` to `"fileHash"` to match the MongoDB alias defined in `ReconciliationFile.file_hash: Field(alias="fileHash")`.

### CR-02: Index `partner_data.trace` should be `partnerData.trace` (data_container)

**Files modified:** `src/models/indexes.py`
**Commit:** 359b0d7
**Applied fix:** Changed nested index field from `"partner_data.trace"` to `"partnerData.trace"` to match `DataContainer.partner_data: Field(alias="partnerData")`.

### CR-03: Index `reconciliation_date` should be `reconciliationDate` (data_container compound)

**Files modified:** `src/models/indexes.py`
**Commit:** 359b0d7
**Applied fix:** Changed compound index field from `"reconciliation_date"` to `"reconciliationDate"` to match `DataContainer.reconciliation_date: Field(alias="reconciliationDate")`.

### CR-04: Index `operation_status` should be `operationStatus` (data_container)

**Files modified:** `src/models/indexes.py`
**Commit:** 359b0d7
**Applied fix:** Changed index field from `"operation_status"` to `"operationStatus"` to match `DataContainer.operation_status: Field(alias="operationStatus")`.

### CR-05: Index `partner_data.status` should be `partnerData.status` (data_container)

**Files modified:** `src/models/indexes.py`
**Commit:** 359b0d7
**Applied fix:** Changed nested index field from `"partner_data.status"` to `"partnerData.status"` to match the MongoDB alias chain.

### CR-06: Index `source_file_id` should be `sourceFileId` (data_container)

**Files modified:** `src/models/indexes.py`
**Commit:** 359b0d7
**Applied fix:** Changed index field from `"source_file_id"` to `"sourceFileId"` to match `DataContainer.source_file_id: Field(alias="sourceFileId")`. This ensures the `find_by_source_file` repository method queries against an indexed field.

### WR-01: `MappingConfigRepository.find_by_version` queries non-existent field

**Files modified:** `src/models/mapping_config.py`
**Commit:** 96ebcd4
**Applied fix:** Added `config_version: Optional[str] = Field(default=None, alias="configVersion")` to the `MappingConfig` model so that `find_by_version` queries against an actual field.

---

_Fixed: 2026-05-27T16:10:00Z_
_Fixer: OpenCode (gsd-code-fixer)_
_Iteration: 1_
