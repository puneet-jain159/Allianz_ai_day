# Allianz Coverage Gap Advisor - Demo Runbook

Live Agent Bricks demo: an AI agent reviews a customer's policy + CRM profile + a described life change and returns a plain-language coverage gaps report with endorsement recommendations.

All assets live in Unity Catalog under `mlops_pj.coverage_gap` on the `DEFAULT` (Azure) workspace.

## What was built

| Component | Type | Identifier |
|---|---|---|
| Allianz Policy Analyst | Knowledge Assistant (real Allianz Home + Motor DOI PDFs) | KA id `924e4b7c-5165-44fb-8985-b6d6962f8a1d`, endpoint `ka-924e4b7c-endpoint` |
| Allianz Customer Profile Analyst | Genie Space (synthetic CRM) | space `01f15eca8e531019982990a65ade688e` |
| classify_life_change | UC Function (ai_query / Claude) | `mlops_pj.coverage_gap.classify_life_change` |
| policy_lookup | UC Function (ai_query over the KA endpoint) - how the supervisor reads the policy | `mlops_pj.coverage_gap.policy_lookup` |
| Allianz Coverage Gap Advisor | Supervisor Agent (orchestrates classifier + Genie + policy_lookup) | MAS id `138f2af1-9ba2-4f8f-a93b-7d5aec8174a0`, endpoint `mas-138f2af1-endpoint` |

The supervisor now **cites the policy section for every gap** (e.g. "Contents section 27 - Liability to the public", "Section 28 - Employer's liability, Silver/Gold only"), pulled live from the DOI booklets via `policy_lookup`. The standalone Policy Analyst KA is still available in the AI Playground for the "ask the policy directly" moment.

Tables: `customers`, `policies`, `assets`, `dependants`, `claims`, `life_events`.

Cover tiers and sublimits in the synthetic data are aligned to the REAL Allianz DOI booklets, so every gap is genuine and defensible.

## Demo personas (synthetic CRM, GBP)

### Persona 1 - Sarah Thompson (flagship: home catering business)
- Home policy `POL-H-1001`, **Bronze** tier, renews **Aug 2026** (~2 months), 2 prior claims, semi-detached home (~450k), one dependant (son, age 4).
- Life change: *"I have started a home catering business from my kitchen and bought 4,800 pounds of equipment including a professional camera for food photography. My niece helps me serve at weekend events."*
- Real policy facts this triggers (Allianz Home DOI):
  - Business equipment sublimit on Bronze = **1,000 GBP** -> 4,800 equipment is **3,800 over**.
  - Business pursuits / business use is excluded under General Exceptions -> no liability for food-related incidents.
  - Liability to domestic employees is **Excluded on Bronze** -> helper (niece) creates uncovered employer liability.
- Recommended endorsements: home business / business equipment endorsement, business public/product liability cover, employers' liability cover.

### Persona 2 - Priya Patel (high-value item)
- Home policy `POL-H-1002`, **Gold** tier. Just got engaged, bought a **6,000 GBP** diamond ring.
- Real policy fact: Valuables single item limit = **2,000 GBP** (all tiers) -> ring is **4,000 over** the single-item limit unless specified.
- Recommendation: specify the ring / add a valuables (specified items) endorsement.

### Persona 3 - James O'Connor (motor business use)
- Motor policy `POL-M-2001`, **Allianz Silver**, use class *Social, Domestic, Pleasure & Commuting*, business use NOT covered.
- Life change: started **Deliveroo food delivery** in his car.
- Real policy fact: business / hire-and-reward use is excluded -> delivery driving is uninsured.
- Recommendation: add hire-and-reward / business use cover.

## Fresh test scenarios (NOT in the guidelines - use these for unbiased testing)

Personas 1-3 above are the supervisor's few-shot **examples/guidelines**, so running them is partly self-confirming. The four personas below (CUST004-007) were added afterwards and appear in **no guideline**, so they test real generalization across Allianz tiers the demo had not used (Home **Silver**, Motor **Essentials**, Motor top-tier **Allianz**). All limits are grounded in the real Allianz DOIs.

### Test A - Daniel Okoye (Home **Silver** - high-value valuables + garden office)
- Policy `POL-H-1003`, Silver, renews **Jul 2026**.
- Prompt: *"Daniel Okoye has inherited a watch and jewellery collection now worth about 28,000 pounds, including a single watch worth 7,500, and has started working from a converted garden office where he keeps about 6,000 pounds of equipment. He has also taken on a part-time gardener. What are his coverage gaps?"*
- Expected gaps (Allianz Home DOI): valuables single-item limit **2,000** vs 7,500 watch (**5,500 over**); valuables total on Silver **20,000** vs ~28,000 collection (**~8,000 over**); business equipment on Silver **5,000** vs 6,000 office kit (**1,000 over**); domestic-employee/employer liability for the gardener (Silver includes 10,000,000 - confirm it is selected). Recommend specified-items/valuables endorsement, business equipment increase, confirm employer liability.

### Test B - Margaret Hughes (Home **Gold** - e-bike, annexe conversion, new resident)
- Policy `POL-H-1004`, Gold, renews **Oct 2026**.
- Prompt: *"Margaret Hughes' elderly mother has moved in permanently, she is converting her garage into an annexe, and she bought a 4,000 pound e-bike she keeps in the garden shed. Are there coverage gaps on her home policy?"*
- Expected gaps: bicycles single-item limit **350** vs 4,000 e-bike (**3,650 over**, and bicycles is optional cover - likely not selected); structural alteration / building works exclusion during the garage conversion; new permanent resident not disclosed (affects contents/occupancy). Recommend specified bicycle/optional bicycle cover, notify insurer of building works, update household composition.

### Test C - Aisha Rahman (Motor **Allianz Essentials** - commute + business use + mods)
- Policy `POL-M-2002`, Allianz Essentials, renews **Nov 2026**.
- Prompt: *"Aisha Rahman has started a 40-mile commute to a new job and occasionally drives to client sites for work. She keeps a 1,500 pound laptop and sample stock in the boot and has fitted aftermarket alloys and an upgraded infotainment system worth about 1,200 pounds. Any gaps on her motor policy?"*
- Expected gaps (Allianz Car DOI): business use (driving to client sites) not covered under *Social, Domestic, Pleasure & Commuting* use class; non-manufacturer in-car equipment covered only **up to 1,000** -> 1,200 mods over-limit AND undisclosed modifications can void cover; personal belongings limit on Essentials **200** vs 1,500 laptop/stock (tools-of-trade likely excluded); Guaranteed Hire Car is not available on Essentials. Recommend business-use class change, declare modifications, review personal-belongings/business-goods cover.

### Test D - Tom Beaumont (Motor top-tier **Allianz** - added driver + track days)
- Policy `POL-M-2003`, Allianz, renews **Jan 2027**.
- Prompt: *"Tom Beaumont wants to let his 19-year-old son drive his car occasionally and has started attending track days a few times a year. Are there coverage gaps on his motor policy?"*
- Expected gaps: son (age 19) is not a named driver on the certificate -> not insured to drive Tom's car; **track days** (defined as racing track/circuit use) are excluded under General Exceptions. Recommend adding the son as a named young driver (note premium/excess impact) and arranging separate track-day cover.

## Three-act demo flow

### Act 1 - The broker problem (30s, slide/talk)
Brokers spend significant time manually reading policy booklets before each renewal conversation. We compress that research to seconds.

### Act 2 - Show the building blocks (2-3 min, AI Playground)
1. **Policy Analyst (KA)** - ask policy questions, get tier-specific answers with citations:
   - "What is the business equipment sublimit on the Allianz Home policy for each cover tier?"
   - "Is business use of the home excluded? Which section?"
   - "On the Motor policy, is using my car for food delivery covered?"
2. **Customer Profile Analyst (Genie)** - ask profile questions:
   - "What is the cover tier, renewal date and business equipment sublimit on Sarah Thompson's home policy?"
   - "List all assets and their values for Sarah Thompson."
   - "How many claims does Sarah Thompson have?"

### Act 3 - The Coverage Gap Advisor end-to-end (3-4 min, AI Playground on the MAS endpoint)
Paste the flagship prompt and let the supervisor orchestrate classify -> profile -> policy -> report:

> Sarah Thompson has started a home catering business and bought 4,800 pounds of equipment including a camera for food photography. Her niece helps at weekend events. What are her coverage gaps and what should I recommend before her renewal?

Expected: a structured report with ~3 gaps (business equipment over-limit by 3,800 GBP, business pursuits exclusion, domestic employee/employer liability excluded on Bronze), each with the policy reference and a named endorsement recommendation.

Then run the motor follow-up to show breadth:

> James O'Connor has started doing food delivery for Deliveroo in his car. Are there any coverage gaps on his motor policy?

### Close (30s)
This is decision support for the broker - grounded in the real policy wording and the customer's actual profile - not customer advice. Same pattern extends to every product line and every CRM field.

## Where to run it
- AI Playground -> select endpoint `mas-138f2af1-endpoint` (the advisor) for Act 3.
- For Act 2, select `ka-924e4b7c-endpoint` (policy) and open the Genie space `Allianz Customer Profile Analyst`.
- Agents page lists the Knowledge Assistant and Supervisor Agent tiles for a UI view.

## Pre-demo checklist
- [ ] KA knowledge source state = `UPDATED` (Agents -> Allianz Policy Analyst). Indexing can take ~10-15 min after creation.
- [ ] Warehouse `ec3b3b85811ecd2c` (or any serverless SQL warehouse) is running for Genie.
- [ ] Run each Act 2 / Act 3 prompt once beforehand to warm endpoints and confirm answers.
- [ ] Confirm the personas resolve by name in Genie (3 flagship + the 4 fresh test personas: Daniel Okoye, Margaret Hughes, Aisha Rahman, Tom Beaumont).

## Notes / troubleshooting
- The supervisor reads policy wording via the `policy_lookup` UC function (an `ai_query` call to the KA endpoint), not the native KA subagent. The native `knowledge_assistant` subagent returns no output inside the supervisor in this workspace - a platform orchestration issue that persisted even after adding the KA via the Agent Bricks UI (see BUILD_GUIDE section 8b for the full RCA). The standalone KA is still great for Act 2.
- If the advisor does not call a tool, re-state the customer by full name and include the life change in one message.
- If Genie cannot resolve a name, ask using the exact full name (e.g. "Sarah Thompson").
- The classifier uses `databricks-claude-sonnet-4-5`; if unavailable, swap the model in `sql/02_create_function.sql` and re-run.
