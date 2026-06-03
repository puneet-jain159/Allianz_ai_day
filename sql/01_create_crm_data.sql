-- =====================================================================
-- Allianz Coverage Gap Analysis POV - Synthetic CRM data
-- Catalog/Schema: mlops_pj.coverage_gap
-- All monetary values in GBP. Cover tiers + sublimits are aligned to the
-- REAL Allianz DOI booklets so the coverage gaps are genuine and defensible:
--   Home (Allianz Home DOI 0038733-2024): Bronze/Silver/Gold
--     - Business equipment sublimit: Bronze 1,000 / Silver 5,000 / Gold 10,000
--     - Valuables single item limit: 2,000 (all tiers)
--     - Liability to domestic employees: Bronze Excluded / Silver-Gold 10,000,000
--   Motor (Allianz Car DOI): Essentials / Silver / Allianz
--     - Use class is Social, Domestic, Pleasure & Commuting by default
--     - Business / hire-and-reward (e.g. food delivery) use is excluded
-- =====================================================================

-- ---------- customers ----------
CREATE OR REPLACE TABLE mlops_pj.coverage_gap.customers AS
SELECT * FROM VALUES
  ('CUST001','Sarah Thompson', DATE'1985-03-12','Marketing Manager','sarah.thompson@email.co.uk','M20 2RN','Manchester',6,'Standard'),
  ('CUST002','Priya Patel',    DATE'1990-07-22','Solicitor',        'priya.patel@email.co.uk',  'EH10 4BF','Edinburgh',3,'Premium'),
  ('CUST003','James O''Connor', DATE'1992-11-05','Software Developer','james.oconnor@email.co.uk','BS7 8QX','Bristol',  2,'Standard'),
  ('CUST004','Daniel Okoye',    DATE'1979-09-30','Architect',         'daniel.okoye@email.co.uk', 'LS6 2AB','Leeds',     5,'Premium'),
  ('CUST005','Margaret Hughes', DATE'1968-02-18','Retired Teacher',   'margaret.hughes@email.co.uk','CF14 3QP','Cardiff',9,'Premium'),
  ('CUST006','Aisha Rahman',    DATE'1994-06-25','Sales Consultant',  'aisha.rahman@email.co.uk', 'B15 2TT','Birmingham',1,'Standard'),
  ('CUST007','Tom Beaumont',    DATE'1983-12-08','Finance Manager',   'tom.beaumont@email.co.uk', 'GU1 1AA','Guildford', 4,'Premium')
AS t(customer_id, full_name, date_of_birth, occupation, email, postcode, city, tenure_years, segment);

-- ---------- policies ----------
CREATE OR REPLACE TABLE mlops_pj.coverage_gap.policies AS
SELECT * FROM VALUES
  ('POL-H-1001','CUST001','Home','Bronze','Active',DATE'2024-08-01',DATE'2026-08-01',320.0,
      500000, 50000, 1000, 2000, 2000, 1000000, 0, 'N/A', false),
  ('POL-H-1002','CUST002','Home','Gold','Active',DATE'2025-09-15',DATE'2026-09-15',540.0,
      1000000, 150000, 10000, 2000, 2000, 2000000, 10000000, 'N/A', false),
  ('POL-M-2001','CUST003','Motor','Allianz Silver','Active',DATE'2025-12-01',DATE'2026-12-01',780.0,
      NULL, NULL, NULL, NULL, 300, 20000000, NULL, 'Social, Domestic, Pleasure & Commuting', false),
  ('POL-H-1003','CUST004','Home','Silver','Active',DATE'2025-07-01',DATE'2026-07-01',480.0,
      1000000, 100000, 5000, 2000, 2000, 2000000, 10000000, 'N/A', false),
  ('POL-H-1004','CUST005','Home','Gold','Active',DATE'2025-10-01',DATE'2026-10-01',610.0,
      1000000, 150000, 10000, 2000, 2000, 2000000, 10000000, 'N/A', false),
  ('POL-M-2002','CUST006','Motor','Allianz Essentials','Active',DATE'2025-11-15',DATE'2026-11-15',690.0,
      NULL, NULL, NULL, NULL, 200, 20000000, NULL, 'Social, Domestic, Pleasure & Commuting', false),
  ('POL-M-2003','CUST007','Motor','Allianz','Active',DATE'2026-01-20',DATE'2027-01-20',950.0,
      NULL, NULL, NULL, NULL, 500, 20000000, NULL, 'Social, Domestic, Pleasure & Commuting', false)
AS t(policy_id, customer_id, product_type, cover_tier, status, start_date, renewal_date, annual_premium_gbp,
     buildings_sum_insured_gbp, contents_sum_insured_gbp, business_equipment_sublimit_gbp,
     valuables_single_item_limit_gbp, personal_belongings_single_item_limit_gbp,
     public_liability_gbp, domestic_employee_liability_gbp, use_class, business_use_covered);

-- ---------- assets ----------
CREATE OR REPLACE TABLE mlops_pj.coverage_gap.assets AS
SELECT * FROM VALUES
  ('A-001','CUST001','Property','Semi-detached family home',450000,DATE'2019-05-01','Home'),
  ('A-002','CUST001','Business Equipment','Catering equipment plus professional camera for food photography',4800,DATE'2026-05-20','Home'),
  ('A-003','CUST002','Jewellery','Diamond engagement ring',6000,DATE'2026-04-10','Home'),
  ('A-004','CUST002','Property','City centre flat',520000,DATE'2023-01-01','Home'),
  ('A-005','CUST003','Vehicle','2021 Volkswagen Golf',18000,DATE'2021-06-01','Driveway'),
  ('A-006','CUST003','Electronics','Camera and gimbal kept in the car for content work',4800,DATE'2026-03-01','Vehicle'),
  ('A-007','CUST004','Jewellery','Inherited watch and jewellery collection, including a single watch valued at 7,500',28000,DATE'2026-02-10','Home'),
  ('A-008','CUST004','Business Equipment','Home office equipment in a converted garden studio',6000,DATE'2026-03-15','Garden office'),
  ('A-009','CUST005','Bicycle','Electric bike kept in the garden shed',4000,DATE'2026-04-22','Garden shed'),
  ('A-010','CUST005','Property','Detached home with garage being converted to an annexe',600000,DATE'2015-06-01','Home'),
  ('A-011','CUST006','Vehicle','2020 Ford Focus',14000,DATE'2020-09-01','Driveway'),
  ('A-012','CUST006','Electronics','Work laptop and sample stock kept in the car boot',1500,DATE'2026-04-01','Vehicle'),
  ('A-013','CUST006','Vehicle Modification','Aftermarket alloy wheels and upgraded infotainment system',1200,DATE'2026-04-05','Vehicle'),
  ('A-014','CUST007','Vehicle','2022 BMW 3 Series (main car)',32000,DATE'2022-03-01','Driveway'),
  ('A-015','CUST007','Vehicle','Classic car kept as a second vehicle',25000,DATE'2026-01-10','Garage')
AS t(asset_id, customer_id, asset_type, description, estimated_value_gbp, acquired_date, location);

-- ---------- dependants ----------
CREATE OR REPLACE TABLE mlops_pj.coverage_gap.dependants AS
SELECT * FROM VALUES
  ('D-001','CUST001','Leo Thompson','Son',4),
  ('D-002','CUST005','Eleanor Hughes','Mother',78),
  ('D-003','CUST007','Jack Beaumont','Son',19)
AS t(dependant_id, customer_id, full_name, relationship, age);

-- ---------- claims ----------
CREATE OR REPLACE TABLE mlops_pj.coverage_gap.claims AS
SELECT * FROM VALUES
  ('CLM-001','CUST001','POL-H-1001',DATE'2023-02-14','Escape of water',3200.0,'Settled'),
  ('CLM-002','CUST001','POL-H-1001',DATE'2024-11-03','Accidental damage',850.0,'Settled'),
  ('CLM-003','CUST002','POL-H-1002',DATE'2025-12-20','Theft',1500.0,'Settled'),
  ('CLM-004','CUST003','POL-M-2001',DATE'2026-01-15','Windscreen',120.0,'Settled'),
  ('CLM-005','CUST004','POL-H-1003',DATE'2025-09-12','Accidental damage',600.0,'Settled'),
  ('CLM-006','CUST006','POL-M-2002',DATE'2026-02-03','Windscreen',95.0,'Settled')
AS t(claim_id, customer_id, policy_id, claim_date, claim_type, amount_gbp, status);

-- ---------- life_events ----------
CREATE OR REPLACE TABLE mlops_pj.coverage_gap.life_events AS
SELECT * FROM VALUES
  ('LE-001','CUST001',DATE'2026-05-22','I have started a home catering business from my kitchen and bought 4,800 pounds of equipment including a professional camera for food photography. My niece helps me serve at weekend events.','Broker note'),
  ('LE-002','CUST002',DATE'2026-04-12','I just got engaged and bought a 6,000 pound diamond engagement ring.','Customer portal'),
  ('LE-003','CUST003',DATE'2026-03-05','I have started doing food delivery for Deliveroo in my car on evenings and weekends to earn extra income.','Broker call'),
  ('LE-004','CUST004',DATE'2026-05-10','I inherited my late father''s watch and jewellery collection, now worth around 28,000 pounds including a single watch worth about 7,500, and I have set up a home office in a converted garden studio with about 6,000 pounds of equipment. I have also taken on a part-time gardener.','Broker note'),
  ('LE-005','CUST005',DATE'2026-05-18','My elderly mother has moved in with us permanently, we are converting the garage into an annexe, and I bought a 4,000 pound electric bike that I keep in the garden shed.','Customer portal'),
  ('LE-006','CUST006',DATE'2026-05-02','I have started a 40-mile commute to a new job and sometimes drive to client sites for work. I keep a work laptop and sample stock worth about 1,500 pounds in the boot and I have fitted aftermarket alloy wheels and an upgraded infotainment system worth around 1,200 pounds.','Broker call'),
  ('LE-007','CUST007',DATE'2026-05-25','I want to let my 19-year-old son drive my car occasionally, and I have started going to a few track days a year at a local circuit.','Broker call')
AS t(event_id, customer_id, event_date, event_description, channel);
