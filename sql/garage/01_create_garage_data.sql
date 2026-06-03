-- =====================================================================
-- Allianz Garage Repair Checker POV - synthetic structured data
-- Catalog/Schema: mlops_pj.garage_checker
-- All monetary values in GBP. VAT at 20%.
--
-- Scenarios (each verdict is defensible from the data + assets):
--   CLM-A  VW Golf      fair repair, matches photo            -> approve
--   CLM-B  Ford Focus   panel-stuffing + inflated hrs/rate    -> flag leakage
--   CLM-C  BMW 320i     costs ok but photo is AI-generated     -> flag imagery
--   CLM-D  Audi A4      genuine severe damage, > total-loss %  -> total loss
-- =====================================================================

-- ---------- vehicles (one row per claimed vehicle, with ACV) ----------
CREATE OR REPLACE TABLE mlops_pj.garage_checker.vehicles AS
SELECT * FROM VALUES
  ('CLM-A','LP21 ZRT','Volkswagen Golf 1.5 TSI Life',2021,'Hatchback',31420,15500),
  ('CLM-B','BV19 KMO','Ford Focus 1.0 EcoBoost Zetec',2019,'Hatchback',54905,9800),
  ('CLM-C','RK20 HWA','BMW 320i M Sport',2020,'Saloon',42110,18000),
  ('CLM-D','YE15 OFN','Audi A4 2.0 TDI S line',2015,'Saloon',98640,8500)
AS t(claim_id, registration, make_model, year, body_style, mileage, acv_gbp);

-- ---------- claims (FNOL + submission metadata) ----------
-- photo_exif_status captures the image-metadata signal used alongside the
-- live visual synthetic-image check. invoice_total_gbp is inclusive of VAT.
CREATE OR REPLACE TABLE mlops_pj.garage_checker.claims AS
SELECT * FROM VALUES
  ('CLM-A','POL-M-3001','LP21 ZRT',DATE'2026-05-11','Low-speed front offside impact in a car park.',
     'Front offside - bumper corner and headlamp', 1,
     'EXIF intact - Apple iPhone 13, GPS Coventry, captured 2026-05-11 14:22, consistent with FNOL.',
     'Northgate Accident Repair Centre', 883.80, 'Open'),
  ('CLM-B','POL-M-3002','BV19 KMO',DATE'2026-05-18','Kerb/collision damage to near-side front while parking.',
     'Near-side front wing', 2,
     'EXIF intact - Samsung SM-G991B, GPS present, captured 2026-05-18, consistent.',
     'Apex Prestige Bodyworks Ltd', 4185.60, 'Open'),
  ('CLM-C','POL-M-3003','RK20 HWA',DATE'2026-05-20','Reported front-end collision - third-party submitted photos.',
     'Front-end - bumper, bonnet, wing, headlamp', 1,
     'EXIF anomaly - no camera make/model, GPS absent, software tag indicates image generation, capture timestamp 2026-05-09 predates the reported incident date.',
     'Citywide Crash Repairs', 3084.96, 'Open'),
  ('CLM-D','POL-M-3004','YE15 OFN',DATE'2026-05-22','Severe frontal collision at speed - vehicle recovered.',
     'Severe frontal collision', 1,
     'EXIF intact - Apple iPhone 12, GPS recovery yard, captured 2026-05-22.',
     'Northgate Accident Repair Centre', 10500.00, 'Open')
AS t(claim_id, policy_ref, vehicle_reg, date_reported, incident_desc, reported_damage_area,
     photo_count, photo_exif_status, garage_name, invoice_total_gbp, status);

-- ---------- rate_guide (standard book times + part prices) ----------
-- Used to benchmark invoice hours and parts. book_hours are the industry
-- standard times; std_labour_rate_gbp is the expected body/paint rate.
CREATE OR REPLACE TABLE mlops_pj.garage_checker.rate_guide AS
SELECT * FROM VALUES
  ('Remove & refit front bumper','Front bumper',1.5,52,NULL,NULL,'R&R only'),
  ('Refinish front bumper','Front bumper',2.0,54,NULL,NULL,'Prep + colour'),
  ('Replace headlamp unit','Headlamp',0.8,52,210,120,'OEM vs aftermarket part'),
  ('Replace front wing','Front wing',2.5,52,320,170,'Includes R&R'),
  ('Refinish front wing','Front wing',2.5,54,NULL,NULL,'Prep + colour + blend'),
  ('Replace front door skin','Front door',4.5,52,540,300,'Major operation'),
  ('Replace bonnet panel','Bonnet',3.0,52,480,260,'Includes R&R'),
  ('Refinish bonnet','Bonnet',2.5,54,NULL,NULL,'Prep + colour'),
  ('Repair rear quarter panel','Rear quarter',6.0,52,NULL,NULL,'Welded panel repair'),
  ('Per-panel refinish/blend','Any',1.5,54,NULL,NULL,'Typical hours per panel for blow-over')
AS t(operation, panel, book_hours, std_labour_rate_gbp, oem_part_gbp, aftermarket_part_gbp, notes);

-- ---------- repair_benchmarks (rates + total-loss threshold) ----------
CREATE OR REPLACE TABLE mlops_pj.garage_checker.repair_benchmarks AS
SELECT * FROM VALUES
  ('standard_body_labour_rate', 52, 'GBP/hour', 'Expected body labour rate for an approved repairer.'),
  ('standard_paint_labour_rate', 54, 'GBP/hour', 'Expected paint labour rate for an approved repairer.'),
  ('total_loss_threshold', 60, 'percent_of_ACV', 'A vehicle is treated as uneconomical to repair (total loss) when the estimated repair cost exceeds this percentage of the pre-accident value (ACV). Repair-to-ACV at or above this routes the claim to a total-loss adjuster before work begins.')
AS t(metric, value, unit, notes);

-- ---------- claim_photos (BINARY content, keyed by claim) ----------
-- Loaded from the photos volume; claim_id derived from the file name prefix
-- (clm_a_* -> CLM-A). Used by the live multimodal assess_damage function.
CREATE OR REPLACE TABLE mlops_pj.garage_checker.claim_photos AS
SELECT
  concat('CLM-', upper(regexp_extract(_metadata.file_name, 'clm_([a-dA-D])_', 1))) AS claim_id,
  _metadata.file_name AS file_name,
  content
FROM read_files('/Volumes/mlops_pj/garage_checker/photos/', format => 'binaryFile');

-- ---------- invoice_files (BINARY content, keyed by claim) ----------
-- Loaded from the invoices volume; claim_id is the CLM-x prefix of the file.
-- Used by the live parse_invoice function.
CREATE OR REPLACE TABLE mlops_pj.garage_checker.invoice_files AS
SELECT
  regexp_extract(_metadata.file_name, '(CLM-[A-D])', 1) AS claim_id,
  _metadata.file_name AS file_name,
  content
FROM read_files('/Volumes/mlops_pj/garage_checker/invoices/', format => 'binaryFile');
