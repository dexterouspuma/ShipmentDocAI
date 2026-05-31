/* ============================================================================
   Reconciliation views — group documents into shipments by shared join keys.
   Run after schema.sql.
   ============================================================================ */

IF OBJECT_ID('dbo.vw_shipment_by_bl', 'V') IS NOT NULL DROP VIEW dbo.vw_shipment_by_bl;
GO

/* All documents that share a Bill of Lading number = one shipment view.
   Lets an analyst see the arrival notice, carrier invoice, and BOL together,
   and spot missing pieces (e.g. a carrier invoice with no matching BOL). */
CREATE VIEW dbo.vw_shipment_by_bl AS
SELECT
    COALESCE(bl_number, mbl_number) AS shipment_bl,
    COUNT(*)                                       AS doc_count,
    SUM(CASE WHEN document_type='arrival_notice'   THEN 1 ELSE 0 END) AS has_arrival_notice,
    SUM(CASE WHEN document_type='carrier_invoice'  THEN 1 ELSE 0 END) AS has_carrier_invoice,
    SUM(CASE WHEN document_type='bol'              THEN 1 ELSE 0 END) AS has_bol,
    SUM(CASE WHEN document_type='packing_list'     THEN 1 ELSE 0 END) AS has_packing_list,
    SUM(CASE WHEN document_type='commercial_invoice' THEN 1 ELSE 0 END) AS has_commercial_invoice,
    MIN(uploaded_at)                               AS first_seen,
    MAX(uploaded_at)                               AS last_seen
FROM dbo.documents
WHERE COALESCE(bl_number, mbl_number) IS NOT NULL
GROUP BY COALESCE(bl_number, mbl_number);
GO

/* Review queue: documents awaiting an analyst, worst-confidence first. */
IF OBJECT_ID('dbo.vw_review_queue', 'V') IS NOT NULL DROP VIEW dbo.vw_review_queue;
GO
CREATE VIEW dbo.vw_review_queue AS
SELECT id, original_filename, document_type, status, bl_number, invoice_ref,
       issuer_name, total_due, currency, min_confidence, page_count, uploaded_at
FROM dbo.documents
WHERE status IN ('extracted','in_review');
GO
