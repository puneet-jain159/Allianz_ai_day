# Allianz Garage Repair Checker - Demo Runbook

Live Agent Bricks demo: an AI agent reviews a motor claim's pre-repair photos and the garage's repair invoice, benchmarks the costs, checks the imagery is genuine, and decides whether to approve, challenge, or route the vehicle to a total-loss adjuster - before any repair work begins.

All assets live in Unity Catalog under `mlops_pj.garage_checker` on the `DEFAULT` (Azure) workspace.

## What was built

| Component | Type | Identifier |
|---|---|---|
| parse_invoice | UC Function - live PDF itemisation (`ai_parse_document` + `ai_query`) | `mlops_pj.garage_checker.parse_invoice` |
| assess_damage | UC Function - **live multimodal** vision (`ai_query` `files =>`, Claude Sonnet) for per-panel damage + AI-image detection | `mlops_pj.garage_checker.assess_damage` |
| Allianz Repair Rate & Vehicle Analyst | Genie Space (vehicles/ACV, claims, rate guide, total-loss threshold) | space `01f15edd7b931af0a5e4fde730e3f0de` |
| policy_lookup | UC Function (`ai_query` over the Allianz Policy Analyst KA - real Motor DOI) | `mlops_pj.garage_checker.policy_lookup` |
| Allianz Garage Repair Checker | Supervisor Agent (orchestrates all four) | MAS id `08625583-...`, endpoint `mas-08625583-endpoint` |

Tables: `vehicles`, `claims`, `rate_guide`, `repair_benchmarks`, `claim_photos` (binary), `invoice_files` (binary).

The agent computes the **repair-to-ACV ratio for every claim** and halts/total-losses anything at or above the 60% threshold. It flags invoice lines billed for panels that the photos show as undamaged, benchmarks hours/rates against the rate guide, and flags imagery that shows signs of AI generation (backed by the photo EXIF status).

## Demo claims (synthetic, GBP)

### CLM-A - VW Golf (clean baseline)
- 2021 VW Golf, ACV 15,500. Photo shows front O/S bumper corner + headlamp damage only. Invoice 883.80 inc VAT, aftermarket parts, book-time hours.
- Expected: **APPROVE** - invoice consistent with the visible damage and standard rates.

### CLM-B - Ford Focus (flagship: inflated / panel-stuffing)
- 2019 Ford Focus, ACV 9,800. Photos show a single damaged N/S front wing; the rest of the car is pristine. Invoice 4,185.60 bills the wing PLUS a front door skin, bonnet and rear quarter, 8-panel paint, OEM parts, and labour at 62/hr.
- Expected: **FLAG - REFER TO ADJUSTER**. ~1,888 billed for undamaged panels (door skin 850, bonnet 666, rear quarter 372), labour rate 10/hr over benchmark, OEM where aftermarket is allowed. ~2,390 challenged cost.

### CLM-C - BMW 320i (synthetic imagery)
- 2020 BMW 320i, ACV 18,000. Invoice 3,084.96 looks plausible, but the submitted photo is AI-generated (warped wheel, melted trim, impossible reflections) and the EXIF shows no camera metadata, a generation software tag, and a capture date before the incident.
- Expected: **FLAG - REFER TO ADJUSTER / SIU**. Imagery cannot be trusted, do not authorise, request genuine photographs.

### CLM-D - Audi A4 (total loss, Phase 2)
- 2015 Audi A4, ACV 8,500. Photo shows severe frontal collision. Invoice 10,500 inc VAT.
- Expected: **TOTAL LOSS - ROUTE TO ADJUSTER**. Repair-to-ACV ~123.5% vs the 60% threshold - halt repair authorisation before work begins.

## Three-act demo flow

### Act 1 - The leakage problem (30s, slide/talk)
Inflated repair invoices and staged/AI-generated damage imagery are a material fraud vector. Catching them at submission - rather than after payment - reduces leakage, and spotting total losses early avoids wasted repair spend on vehicles that should be written off.

### Act 2 - Show the building blocks (3-4 min, AI Playground)
1. **Damage photo analyst (live vision)** - the wow moment. In the Playground, select `databricks-claude-sonnet-4-5`, drag in `assets/photos/clm_c_synthetic.png`, and ask: *"Assess the vehicle damage by panel and tell me whether this looks like a genuine photograph or an AI-generated image."* It flags the synthetic artefacts. Repeat with `clm_b_focus_wing.png` to show it correctly reads a genuine single-wing dent. (Or run the function: `SELECT assess_damage('CLM-C');`.)
2. **Invoice itemiser (live)** - `SELECT parse_invoice('CLM-B');` returns the full itemised JSON from the PDF.
3. **Rate & Vehicle Analyst (Genie)** - ask: *"What is the ACV for claim CLM-D and the total-loss threshold?"*, *"What is the standard book time and labour rate to replace a front wing?"*

### Act 3 - The Garage Repair Checker end-to-end (4-5 min, AI Playground on the MAS endpoint)
Select endpoint `mas-08625583-endpoint` and run the flagship:

> Review claim CLM-B and tell me if the repair invoice is justified.

Expected: itemised invoice, a photo-vs-invoice cross-check naming the undamaged panels billed (~1,888), the rate/hours over-billing, OEM-vs-aftermarket point cited from the policy, repair-to-ACV well under threshold, and a FLAG verdict with a ~2,390 leakage estimate.

Then show breadth with two more:

> Check claim CLM-C before we authorise the repair.

(Synthetic imagery -> do not authorise, route to SIU, request genuine photos.)

> Should we repair the vehicle on claim CLM-D?

(Total loss -> repair ~123.5% of ACV, halt repair, route to total-loss adjuster.)

Optionally open with **CLM-A** to show a clean approve.

### Close (30s)
This is decision support for the claims handler - grounded in the actual photos, the invoice wording, the rate guide and the real policy - not a final coverage decision. The same pattern extends to every repair network and every claim type, and Phase 2 (early total-loss routing) avoids repair spend on write-offs.

## Where to run it
- AI Playground -> endpoint `mas-08625583-endpoint` (the checker) for Act 3.
- AI Playground -> `databricks-claude-sonnet-4-5` with an uploaded photo for the live vision moment, or run `assess_damage` / `parse_invoice` from a SQL editor.
- Genie -> "Allianz Repair Rate & Vehicle Analyst" space for the benchmarking agent alone.

## Pre-demo checklist
- [ ] Warehouse `ec3b3b85811ecd2c` (or any serverless SQL warehouse, DBR 17.1+) is running.
- [ ] Photos and invoices are present in the volumes (`databricks fs ls dbfs:/Volumes/mlops_pj/garage_checker/photos/`).
- [ ] Allianz Policy Analyst KA endpoint `ka-924e4b7c-endpoint` is running (powers `policy_lookup`).
- [ ] Warm the MAS endpoint with each Act 3 prompt once beforehand - a full run is ~3-4 minutes as it parses the PDF, runs vision on each photo, queries Genie and the policy KA.
- [ ] Confirm `SELECT assess_damage('CLM-C')` returns `AUTHENTICITY: SUSPECTED SYNTHETIC` and `assess_damage('CLM-B')` returns `GENUINE`.

## Notes / troubleshooting
- The agent reads policy wording via the `policy_lookup` UC function (an `ai_query` call to the KA endpoint), the same reliable pattern as the Coverage Gap demo (the native KA subagent returns no output inside a supervisor in this workspace - see the Coverage Gap BUILD_GUIDE section 8b).
- Photo analysis is genuinely live: `assess_damage` calls a vision model on the stored image bytes at request time. If you want to demo a brand-new image, drop it into the photos volume named `clm_<x>_*.png` and reload `claim_photos`, or just upload it directly in the Playground vision chat.
- If a tool is skipped, restate the request as "Review claim CLM-B" with the exact claim id.
- `assess_damage` uses `databricks-claude-sonnet-4-5` for vision; if unavailable, swap to `databricks-llama-4-maverick` in `sql/garage/03_assess_damage.sql` and re-run.
- The rate guide intentionally covers common body operations; for the severe CLM-D job the agent reasons that the structural scope is consistent with the visible damage and correctly proceeds to the total-loss decision rather than flagging leakage.
