# Future Phases Plan — Reconciliation & Beyond

## Overview

Phases 01–07 (Ingestion Pipeline) are complete. The following phases outline the reconciliation engine, compensation workflow, and reporting/dashboard capabilities that build on the existing foundation.

---

## Phase 8: Reconciliation Engine

**Goal:** Match transactions between partner data and internal records, detect discrepancies, and store reconciliation results.

**Requirements:**
- RECON-01: Fetch transactions from 2 sources (partner data_container + internal system)
- RECON-02: Match engine — match by trace, date range, amount tolerance
- RECON-03: Discrepancy detection — amount mismatch, status mismatch, missing transactions
- RECON-04: Result storage — matched/unmatched/discrepancy records with reason codes

**Proposed Plans:**

| Plan | Objective | Key Files |
|------|-----------|-----------|
| 08-01 | DataFetcher service — fetch transactions from data_container and external source | `src/reconciliation/fetcher.py` |
| 08-02 | MatchEngine — match transactions by composite key with configurable tolerance | `src/reconciliation/match_engine.py` |
| 08-03 | DiscrepancyDetector — compare matched pairs, flag differences | `src/reconciliation/discrepancy.py` |
| 08-04 | ReconciliationResult model + repository — store match results | `src/models/reconciliation_result.py` |
| 08-05 | ReconciliationPipeline — orchestrate fetch → match → detect → store | `src/reconciliation/pipeline.py` |
| 08-06 | Integration tests — realistic reconciliation scenarios | `tests/test_reconciliation.py` |

**Key Design Decisions:**
- Matching key: `identify + reconciliationDate + trace` (same as ingestion duplicate key)
- Amount tolerance: configurable (e.g., ±1 VND for rounding differences)
- Match types: EXACT_MATCH, AMOUNT_MISMATCH, STATUS_MISMATCH, MISSING_PARTNER, MISSING_INTERNAL
- Result model stores both sides of the match for audit trail

**Data Model (new collection: `reconciliation_result`):**
```json
{
  "_id": "uuid",
  "reconciliationDate": "2024-07-07",
  "partner": "MOMO",
  "workflowType": "UPC",
  "matchType": "EXACT_MATCH | AMOUNT_MISMATCH | STATUS_MISMATCH | MISSING_PARTNER | MISSING_INTERNAL",
  "partnerTransaction": { ... DataContainer reference ... },
  "internalTransaction": { ... internal system reference ... },
  "discrepancy": {
    "field": "amount",
    "partnerValue": 259200,
    "internalValue": 259199,
    "difference": 1
  },
  "status": "PENDING | RESOLVED | ESCALATED",
  "resolvedBy": "system | user",
  "resolvedAt": "ISODate",
  "createdAt": "ISODate"
}
```

**Indexes:**
- `reconciliationDate + partner + workflowType` (compound)
- `matchType` (filter by discrepancy type)
- `status` (filter pending vs resolved)

---

## Phase 9: Compensation Workflow

**Goal:** Auto-create compensation transactions for identified discrepancies, with retry and escalation support.

**Requirements:**
- COMP-01: Compensation rule engine — define rules for each discrepancy type
- COMP-02: Auto-generate compensation transactions (adjustment entries)
- COMP-03: Retry orchestration — retry failed compensations with exponential backoff
- COMP-04: Escalation — flag unresolved discrepancies after N retries

**Proposed Plans:**

| Plan | Objective | Key Files |
|------|-----------|-----------|
| 09-01 | CompensationRule model + engine — rules per discrepancy type | `src/compensation/rules.py` |
| 09-02 | CompensationGenerator — create adjustment transactions | `src/compensation/generator.py` |
| 09-03 | RetryOrchestrator — exponential backoff, max retries | `src/compensation/retry.py` |
| 09-04 | CompensationResult model + repository | `src/models/compensation_result.py` |
| 09-05 | CompensationPipeline — orchestrate rule → generate → retry | `src/compensation/pipeline.py` |
| 09-06 | Integration tests — compensation scenarios | `tests/test_compensation.py` |

**Key Design Decisions:**
- Compensation rules stored in MongoDB (config-driven, like MappingConfig)
- Each compensation transaction links back to original discrepancy
- Retry: configurable max attempts, backoff multiplier, jitter
- Escalation: after max retries, mark as ESCALATED for manual review

**Data Model (new collection: `compensation_result`):**
```json
{
  "_id": "uuid",
  "reconciliationResultId": "uuid",
  "compensationType": "ADJUSTMENT | REFUND | REVERSAL",
  "amount": Decimal128,
  "currency": "VND",
  "status": "PENDING | SUCCESS | FAILED | ESCALATED",
  "retryCount": 0,
  "maxRetries": 3,
  "nextRetryAt": "ISODate",
  "error": null,
  "createdAt": "ISODate",
  "updatedAt": "ISODate"
}
```

---

## Phase 10: Dashboard & Reporting

**Goal:** Provide visibility into ingestion, reconciliation, and compensation status via reports and API endpoints.

**Requirements:**
- REPORT-01: Ingestion summary — files processed, success/failure rates, duration
- REPORT-02: Reconciliation summary — match rates, discrepancy breakdown by type
- REPORT-03: Compensation summary — success rates, pending/escalated counts
- REPORT-04: Partner onboarding report — config validation, test file processing

**Proposed Plans:**

| Plan | Objective | Key Files |
|------|-----------|-----------|
| 10-01 | ReportGenerator service — aggregate stats from all collections | `src/reports/generator.py` |
| 10-02 | IngestionReport — file-level and row-level statistics | `src/reports/ingestion.py` |
| 10-03 | ReconciliationReport — match rates, discrepancy breakdown | `src/reports/reconciliation.py` |
| 10-04 | CompensationReport — success rates, retry analysis | `src/reports/compensation.py` |
| 10-05 | API endpoints (FastAPI) — expose reports as REST API | `src/api/reports.py` |
| 10-06 | Dashboard templates (HTML/JSON) — simple web UI | `src/api/templates/` |

**Key Design Decisions:**
- Reports generated on-demand (no pre-computed aggregates)
- MongoDB aggregation pipelines for efficient queries
- API returns JSON — frontend can be added later
- Simple HTML templates for quick visibility

**Report Output Example (JSON):**
```json
{
  "ingestion": {
    "totalFiles": 150,
    "successFiles": 145,
    "failedFiles": 5,
    "totalRows": 500000,
    "successRows": 495000,
    "failedRows": 5000,
    "avgDurationMs": 2345
  },
  "reconciliation": {
    "totalTransactions": 495000,
    "exactMatches": 490000,
    "amountMismatches": 3000,
    "statusMismatches": 1000,
    "missingPartner": 500,
    "missingInternal": 500,
    "matchRate": 98.99
  },
  "compensation": {
    "totalCompensations": 4500,
    "success": 4200,
    "failed": 200,
    "escalated": 100,
    "successRate": 93.33
  }
}
```

---

## Dependency Graph

```
Phase 07 (Logging) ──────────────────────────────────────────┐
                                                              │
Phase 06 (Pipeline) ──▶ Phase 08 (Reconciliation Engine) ──▶ Phase 09 (Compensation)
                                                              │
                                                              ▼
                                                      Phase 10 (Dashboard)
```

## Estimated Effort

| Phase | Complexity | Estimated Plans | Estimated Tests |
|-------|-----------|-----------------|-----------------|
| 08 | High | 6 | ~80 |
| 09 | Medium | 6 | ~60 |
| 10 | Medium | 6 | ~40 |

## Tech Stack Additions

| Component | Technology |
|-----------|------------|
| API Framework | FastAPI (for Phase 10) |
| Scheduler | APScheduler (for retry orchestration) |
| HTML Templates | Jinja2 (for simple dashboard) |
