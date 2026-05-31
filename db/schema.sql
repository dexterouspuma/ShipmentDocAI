/* ============================================================================
   Shipment Document AI — Azure SQL schema (T-SQL / SQL Server flavor)
   ----------------------------------------------------------------------------
   Design: hybrid.
     - Relational columns for fields we filter, sort, and JOIN on (the shipment
       reconciliation keys) -> fast queries + indexes.
     - Full extracted payload kept as JSON (extracted_json) for complete fidelity
       and forward-compatibility as the schema evolves.
     - Repeating sections (parties, charges, goods lines) as child tables so they
       are queryable; the JSON remains the source of truth for full detail.
   Run order matters (foreign keys). Idempotent-ish: drops then recreates.
   ============================================================================ */

IF OBJECT_ID('dbo.audit_log', 'U')          IS NOT NULL DROP TABLE dbo.audit_log;
IF OBJECT_ID('dbo.document_goods_lines','U') IS NOT NULL DROP TABLE dbo.document_goods_lines;
IF OBJECT_ID('dbo.document_charges', 'U')    IS NOT NULL DROP TABLE dbo.document_charges;
IF OBJECT_ID('dbo.document_parties', 'U')    IS NOT NULL DROP TABLE dbo.document_parties;
IF OBJECT_ID('dbo.documents', 'U')           IS NOT NULL DROP TABLE dbo.documents;
GO

/* ---------------------------------------------------------------------------
   documents — one row per ingested PDF; tracks lifecycle + denormalized summary
   --------------------------------------------------------------------------- */
CREATE TABLE dbo.documents (
    id                  UNIQUEIDENTIFIER    NOT NULL DEFAULT NEWID() PRIMARY KEY,
    original_filename   NVARCHAR(400)       NOT NULL,
    blob_path_raw       NVARCHAR(800)       NOT NULL,
    blob_path_processed NVARCHAR(800)       NULL,

    document_type       VARCHAR(40)         NOT NULL DEFAULT 'unknown'
        CONSTRAINT CK_documents_type CHECK (document_type IN
        ('arrival_notice','commercial_invoice','carrier_invoice','packing_list','bol','unknown')),
    transport_mode      VARCHAR(20)         NOT NULL DEFAULT 'unknown'
        CONSTRAINT CK_documents_mode CHECK (transport_mode IN
        ('ocean_fcl','ocean_lcl','air','unknown')),
    status              VARCHAR(30)         NOT NULL DEFAULT 'uploaded'
        CONSTRAINT CK_documents_status CHECK (status IN
        ('uploaded','queued','extracting','extracted','extraction_failed',
         'in_review','approved','rejected','cover_sheet_generated')),

    /* --- denormalized join / reconciliation keys (see schemas/README.md) --- */
    bl_number           NVARCHAR(60)        NULL,
    mbl_number          NVARCHAR(60)        NULL,
    hbl_number          NVARCHAR(60)        NULL,
    invoice_ref         NVARCHAR(60)        NULL,
    container_no        NVARCHAR(40)        NULL,
    reference_no        NVARCHAR(80)        NULL,
    issuer_name         NVARCHAR(200)       NULL,
    total_due           DECIMAL(14,2)       NULL,
    currency            VARCHAR(8)          NULL,

    /* --- full extracted payload (shared.models.ExtractedDocument as JSON) --- */
    extracted_json      NVARCHAR(MAX)       NULL
        CONSTRAINT CK_documents_json CHECK (extracted_json IS NULL OR ISJSON(extracted_json) = 1),
    /* lowest field-level confidence in the doc, for review triage */
    min_confidence      DECIMAL(5,4)        NULL,

    /* --- lifecycle metadata --- */
    page_count          INT                 NULL,
    uploaded_by         NVARCHAR(200)       NULL,
    uploaded_at         DATETIME2(0)        NOT NULL DEFAULT SYSUTCDATETIME(),
    extracted_at        DATETIME2(0)        NULL,
    reviewed_by         NVARCHAR(200)       NULL,
    reviewed_at         DATETIME2(0)        NULL,
    error_message       NVARCHAR(1000)      NULL
);
GO

CREATE INDEX IX_documents_status        ON dbo.documents (status) INCLUDE (document_type, uploaded_at);
CREATE INDEX IX_documents_bl_number     ON dbo.documents (bl_number);
CREATE INDEX IX_documents_invoice_ref   ON dbo.documents (invoice_ref);
CREATE INDEX IX_documents_container_no  ON dbo.documents (container_no);
CREATE INDEX IX_documents_uploaded_at   ON dbo.documents (uploaded_at DESC);
GO

/* ---------------------------------------------------------------------------
   document_parties — shipper / consignee / notify / broker (repeating)
   --------------------------------------------------------------------------- */
CREATE TABLE dbo.document_parties (
    id              BIGINT IDENTITY(1,1) PRIMARY KEY,
    document_id     UNIQUEIDENTIFIER NOT NULL
        CONSTRAINT FK_parties_doc REFERENCES dbo.documents(id) ON DELETE CASCADE,
    role            VARCHAR(20)     NOT NULL,   -- SHIPPER|CONSIGNEE|NOTIFY|BROKER
    name            NVARCHAR(300)   NULL,
    address         NVARCHAR(600)   NULL,
    contact_tel     NVARCHAR(80)    NULL,
    contact_email   NVARCHAR(200)   NULL,
    confidence      DECIMAL(5,4)    NULL
);
GO
CREATE INDEX IX_parties_document ON dbo.document_parties (document_id);
GO

/* ---------------------------------------------------------------------------
   document_charges — destination charges / freight charge lines (repeating)
   --------------------------------------------------------------------------- */
CREATE TABLE dbo.document_charges (
    id              BIGINT IDENTITY(1,1) PRIMARY KEY,
    document_id     UNIQUEIDENTIFIER NOT NULL
        CONSTRAINT FK_charges_doc REFERENCES dbo.documents(id) ON DELETE CASCADE,
    line_no         INT             NULL,
    description     NVARCHAR(300)   NULL,
    basis           NVARCHAR(80)    NULL,
    rate            DECIMAL(14,2)   NULL,
    amount          DECIMAL(14,2)   NULL,
    confidence      DECIMAL(5,4)    NULL
);
GO
CREATE INDEX IX_charges_document ON dbo.document_charges (document_id);
GO

/* ---------------------------------------------------------------------------
   document_goods_lines — invoice / packing-list line items (repeating)
   --------------------------------------------------------------------------- */
CREATE TABLE dbo.document_goods_lines (
    id              BIGINT IDENTITY(1,1) PRIMARY KEY,
    document_id     UNIQUEIDENTIFIER NOT NULL
        CONSTRAINT FK_goods_doc REFERENCES dbo.documents(id) ON DELETE CASCADE,
    line_no         INT             NULL,
    description     NVARCHAR(400)   NULL,
    hs_code         NVARCHAR(40)    NULL,
    quantity        DECIMAL(14,3)   NULL,
    unit            NVARCHAR(20)    NULL,
    unit_price      DECIMAL(14,4)   NULL,
    amount          DECIMAL(14,2)   NULL,
    cartons         INT             NULL,
    net_weight_kg   DECIMAL(14,3)   NULL,
    gross_weight_kg DECIMAL(14,3)   NULL,
    dimensions_cm   NVARCHAR(60)    NULL,
    confidence      DECIMAL(5,4)    NULL
);
GO
CREATE INDEX IX_goods_document ON dbo.document_goods_lines (document_id);
GO

/* ---------------------------------------------------------------------------
   audit_log — who did what during review (immutable trail)
   --------------------------------------------------------------------------- */
CREATE TABLE dbo.audit_log (
    id              BIGINT IDENTITY(1,1) PRIMARY KEY,
    document_id     UNIQUEIDENTIFIER NOT NULL
        CONSTRAINT FK_audit_doc REFERENCES dbo.documents(id) ON DELETE CASCADE,
    action          VARCHAR(30)     NOT NULL
        CONSTRAINT CK_audit_action CHECK (action IN
        ('opened','edited_field','approved','rejected','sent_back','generated_cover_sheet')),
    actor           NVARCHAR(200)   NOT NULL,
    field_name      NVARCHAR(100)   NULL,
    old_value       NVARCHAR(MAX)   NULL,
    new_value       NVARCHAR(MAX)   NULL,
    timestamp       DATETIME2(0)    NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
CREATE INDEX IX_audit_document ON dbo.audit_log (document_id, timestamp);
GO
