// Initialize MongoDB collections and indexes for Reconciliation Ingestion Platform

db = db.getSiblingDB("reconciliation");

// Create collections (explicit creation for clarity)
db.createCollection("reconciliation_file");
db.createCollection("reconciliation_mapping_config");
db.createCollection("data_container");

// reconciliation_file indexes
db.reconciliation_file.createIndex(
  { fileHash: 1 },
  { unique: true, name: "idx_file_hash_unique" }
);
db.reconciliation_file.createIndex(
  { partner: 1, reconciliationDate: 1 },
  { name: "idx_partner_date" }
);

// reconciliation_mapping_config indexes
db.reconciliation_mapping_config.createIndex(
  { partner: 1, workflowType: 1, fileType: 1 },
  { name: "idx_partner_workflow_type" }
);

// data_container indexes
db.data_container.createIndex(
  { "partnerData.trace": 1 },
  { name: "idx_trace" }
);
db.data_container.createIndex(
  { identify: 1, reconciliationDate: 1 },
  { name: "idx_identify_date" }
);
db.data_container.createIndex(
  { operationStatus: 1 },
  { name: "idx_operation_status" }
);
db.data_container.createIndex(
  { "partnerData.status": 1 },
  { name: "idx_partner_status" }
);
db.data_container.createIndex(
  { sourceFileId: 1 },
  { name: "idx_source_file" }
);

print("MongoDB initialized successfully — all collections and indexes created.");
