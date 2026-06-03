-- =====================================================================
-- UC Function: parse_invoice(claim_id)
-- Live, end-to-end invoice itemisation. Reads the claim's garage invoice
-- PDF from the invoice_files table, parses it with ai_parse_document, then
-- uses ai_query (Claude) to return a clean itemised JSON of every line.
-- This is the "Extract and itemise repair costs from invoice PDFs"
-- capability, run live at agent-call time.
-- =====================================================================
CREATE OR REPLACE FUNCTION mlops_pj.garage_checker.parse_invoice(in_claim_id STRING)
RETURNS STRING
COMMENT 'Parses the garage repair invoice PDF for a given claim id (e.g. "CLM-B") and returns a JSON object with the garage name, invoice number, date, vehicle, registration, labour_rate_gbp, an itemised line_items array (each with section [Parts/Labour/Paint/Sublet], description, qty_or_hours, unit, unit_price_gbp, amount_gbp), and subtotal_gbp / vat_gbp / total_gbp. Itemises costs exactly as written on the invoice. Call this to read and break down what the garage is charging before benchmarking the costs.'
RETURN (
  SELECT ai_query(
    'databricks-claude-sonnet-4-5',
    CONCAT(
      'You are an insurance claims invoice parser for a UK motor insurer. The following JSON is the parsed ',
      'content of a garage repair invoice (tables are embedded as HTML). Extract the invoice faithfully into a ',
      'single JSON object with these fields: garage_name, invoice_no, date, vehicle, registration, ',
      'labour_rate_gbp (number), line_items (array of objects with: section one of [Parts, Labour, Paint, Sublet], ',
      'description, qty_or_hours (number), unit, unit_price_gbp (number), amount_gbp (number)), ',
      'subtotal_gbp (number), vat_gbp (number), total_gbp (number). ',
      'Use only what is on the invoice - do not invent or merge lines, and keep hours as hours and parts as units. ',
      'Return ONLY the JSON object - no prose, no explanation, and no markdown code fences. ',
      'Parsed invoice content: ',
      to_json(ai_parse_document(content):document:elements)
    )
  )
  FROM mlops_pj.garage_checker.invoice_files
  WHERE claim_id = in_claim_id
  LIMIT 1
);
