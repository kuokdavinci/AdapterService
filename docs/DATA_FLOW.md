# Data Flow

## End-to-End Flow

```
User calls: pipeline.process_file(
    file_path="m4becomvsp_07072024_combine.xlsx",
    partner="MOMO",
    workflow_type="UPC",
    file_type=FileType.SETTLEMENT,
    reconciliation_date=datetime(2024, 7, 7),
)
```

### Step 1: File Hash & Duplicate Check

```
_compute_file_hash(file_path)
  → Reads file content in 8KB chunks (async via thread pool)
  → Returns SHA256 hex string

_recon_repo.find_by_file_hash(hash)
  → Query: {"fileHash": hash}
  → If found: return existing record + error (duplicate)
  → If not found: continue
```

### Step 2: Create Tracking Record

```
ReconciliationFile(
    partner="MOMO",
    file_name="m4becomvsp_07072024_combine.xlsx",
    file_hash="<sha256>",
    file_type=FileType.SETTLEMENT,
    reconciliation_date=datetime(2024, 7, 7),
    processing_status=ProcessingStatus.PROCESSING,
)
→ _recon_repo.create() → INSERT into reconciliation_file
→ Logger: emit_file_started(file_id, file_name, partner)
```

### Step 3: Load Mapping Configuration

```
_config_loader.load_by_partner_type("MOMO", "UPC", FileType.SETTLEMENT)
  → Cache check: "MOMO:UPC:SETTLEMENT:latest"
  → If hit: return cached config
  → If miss:
    → _repository.find_by_partner_and_type("MOMO", "UPC", "SETTLEMENT")
    → Query: {"partner": "MOMO", "workflowType": "UPC", "fileType": "SETTLEMENT"}
    → ConfigValidator.validate(config)
    → Cache put with TTL 300s
    → Return config
```

**Config structure returned:**
```json
{
  "partner": "MOMO",
  "workflowType": "UPC",
  "sheetName": "Sheet1",
  "startRow": 2,
  "fieldMappings": [
    { "path": "id", "column": "A", "type": "STRING", "required": true },
    { "path": "trace", "column": "J", "type": "STRING" },
    { "path": "amount", "column": "D", "type": "DECIMAL" },
    { "path": "currency", "constant": "VND", "type": "CONSTANT" },
    { "path": "status", "column": "Q", "type": "MAPPING",
      "mapping": { "Thành công": "SUCCESS", "others": "FAILED" } },
    { "path": "transDate", "column": "B", "type": "DATE" }
  ]
}
```

### Step 4: Create Reader

```
ExcelStreamReader.from_mapping_config(file_path, config)
  → sheet_name=config.sheet_name ("Sheet1")
  → start_row=config.start_row (2)
  → skip_empty_rows=True
  → Opens workbook in read_only=True mode
```

### Step 5: Process Each Row

**Example Excel row (row 2, after header):**

| A | B | C | D | ... | J | ... | Q |
|---|---|---|---|-----|---|-----|---|
| 61838642196 | 2024-07-05 | | 259200 | ... | 2407055711887385978413624 | ... | Thành công |

#### 5a: Convert tuple to dict

```python
row_tuple = ("61838642196", "2024-07-05", None, 259200, ..., "2407055711887385978413624", ..., "Thành công")
row_dict = {"A": "61838642196", "B": "2024-07-05", "C": None, "D": 259200, "J": "2407055711887385978413624", "Q": "Thành công"}
```

#### 5b: Normalize

```python
normalizer = TransactionNormalizer(config.field_mappings)
norm_result = normalizer.normalize(row_dict, row_number=2)
```

**Processing each FieldMapping:**

| Mapping | Source | Conversion | Result |
|---------|--------|------------|--------|
| `id` (STRING, col A) | `"61838642196"` | str() | `"61838642196"` |
| `trace` (STRING, col J) | `"2407055711887385978413624"` | str() | `"2407055711887385978413624"` |
| `amount` (DECIMAL, col D) | `259200` | Decimal(259200) | `Decimal('259200')` |
| `currency` (CONSTANT) | — | constant value | `"VND"` |
| `status` (MAPPING, col Q) | `"Thành công"` | mapping lookup | `"SUCCESS"` |
| `transDate` (DATE, col B) | `"2024-07-05"` | strptime("%Y-%m-%d") | `datetime(2024, 7, 5)` |

**Result:**
```python
NormalizationResult(
    data={
        "id": "61838642196",
        "trace": "2407055711887385978413624",
        "amount": Decimal("259200"),
        "currency": "VND",
        "status": "SUCCESS",
        "transDate": datetime(2024, 7, 5),
    },
    errors=[],
)
```

#### 5c: Build CanonicalTransaction

```python
txn, build_errors = TransactionNormalizer.build_canonical(norm_result.data, [], row_number=2)
```

**Result:**
```python
CanonicalTransaction(
    id="61838642196",
    trace="2407055711887385978413624",
    amount=Decimal("259200"),
    currency="VND",
    status=TransactionStatus.SUCCESS,
    transDate=datetime(2024, 7, 5),
    extra={},
)
```

#### 5d: Validate

```python
validator = Validator(data_container_repo=self._data_repo, reconciliation_file_repo=self._recon_repo)
validation_result = await validator.validate_with_duplicates(
    txn,
    identify="MOMO",
    reconciliation_date=datetime(2024, 7, 7),
    file_hash="<sha256>",
    row_number=2,
    trace="2407055711887385978413624",
)
```

**Checks performed:**
1. Required fields: id ✓, currency ✓
2. Decimal non-negative: 259200 >= 0 ✓
3. Date type: datetime ✓
4. Status enum: SUCCESS in TransactionStatus ✓
5. Transaction duplicate: query `{"identify": "MOMO", "reconciliationDate": datetime(2024,7,7), "partnerData.trace": "2407055711887385978413624"}` → None ✓
6. File duplicate: query `{"fileHash": "<sha256>"}` → None ✓

**Result:** `ValidationResult(is_valid=True, errors=[])`

#### 5e: Persist

```python
partner_data = PartnerData(
    _id="61838642196",
    trace="2407055711887385978413624",
    status="SUCCESS",
    amount=Decimal("259200"),
    currency="VND",
    transDate=datetime(2024, 7, 5),
    extra={},
)
data_container = DataContainer(
    identify="MOMO",
    workflow_type="UPC",
    reconciliation_date=datetime(2024, 7, 7),
    source_file_id=file_record.id,
    partner_data=partner_data,
)
batch_buffer.append(data_container)
```

**Logger:** `emit_row_success(file_id, row_number=2, trace="2407055711887385978413624")`

#### 5f: Batch Flush

```python
if len(batch_buffer) >= 100:  # batch_size
    inserted = await self._flush_batch(batch_buffer)
    success_rows += inserted  # Uses actual insert count
    batch_buffer = []
```

**MongoDB operation:**
```python
collection.insert_many([
    doc.model_dump(by_alias=True, exclude_none=False)
    for doc in batch_buffer
])
```

### Step 6: Final Flush & Stats Update

```python
# Flush remaining
if batch_buffer:
    inserted = await self._flush_batch(batch_buffer)
    success_rows += inserted

# Update stats
await _recon_repo.update_processing_stats(file_record.id, total_rows, success_rows, failed_rows)
await _recon_repo.update_status(file_record.id, ProcessingStatus.COMPLETED)

# Update in-memory record
file_record.processing_status = ProcessingStatus.COMPLETED
file_record.total_rows = total_rows
file_record.success_rows = success_rows
file_record.failed_rows = failed_rows
```

### Step 7: Return Result

```python
duration_ms = (time.monotonic() - start_time) * 1000
logger.emit_file_completed(file_id, total_rows, success_rows, failed_rows, duration_ms)

return IngestionResult(
    file_record=file_record,
    stats=ProcessingStats(total_rows=1000, success_rows=990, failed_rows=10),
    errors=[
        {"row": 142, "field": "amount", "reason": "invalid decimal value: 'abc'"},
        ...
    ],
)
```

## Error Scenarios

### Scenario 1: Invalid Row

**Input:** Row with `amount = "abc"`

```
normalize() → _convert_decimal("abc") → InvalidOperation
  → ValidationError(field="amount", reason="invalid decimal value: 'abc'")
  → norm_result.errors not empty
  → failed_rows += 1
  → errors.append({"row": 142, "field": "amount", "reason": "..."})
  → logger.emit_row_failed(file_id, 142, "", "invalid decimal value: 'abc'")
  → continue (next row)
```

### Scenario 2: Duplicate Transaction

**Input:** Row with trace already in data_container

```
validate_with_duplicates() → _check_transaction_duplicate()
  → Query returns existing document
  → ValidationError(field="duplicate", reason="transaction already exists")
  → failed_rows += 1
  → continue (next row)
```

### Scenario 3: Duplicate File

**Input:** Same file re-uploaded

```
_compute_file_hash() → SHA256 matches existing record
  → find_by_file_hash() returns existing
  → emit_file_failed("duplicate", "File already processed")
  → return IngestionResult(file_record=existing, errors=[{"field": "file_duplicate", ...}])
```

### Scenario 4: Exception During Processing

**Input:** ConfigLoader fails to connect to MongoDB

```
process_file() → ConfigLoader.load_by_partner_type() → Exception
  → except block:
    → emit_file_failed(file_id, "Connection refused")
    → update_status(FAILED)  # best effort
    → return IngestionResult(file_record=file_record, stats=partial_stats, errors=[{"field": "pipeline", ...}])
```
