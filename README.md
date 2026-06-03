# Allianz AI Day — Agent Bricks Demos

Two end-to-end **Databricks Agent Bricks Supervisor Agent** demos built for insurance use cases. Each agent orchestrates a mix of UC Functions, a Genie Space, and a Knowledge Assistant over real Allianz policy documents.

| Demo | What it does | Build guide | Runbook |
|---|---|---|---|
| **Coverage Gap Advisor** | Reviews a customer's policy, CRM profile, and a described life change, then returns a plain-language coverage-gaps report with endorsement recommendations. | [`BUILD_GUIDE.md`](BUILD_GUIDE.md) | [`DEMO_RUNBOOK.md`](DEMO_RUNBOOK.md) |
| **Garage Repair Checker** | Reviews a motor claim's pre-repair photos + garage invoice, benchmarks against a rate guide and the real Motor policy, and flags over-charging, AI-generated images, and total-loss cases (live multimodal). | [`GARAGE_BUILD_GUIDE.md`](GARAGE_BUILD_GUIDE.md) | [`GARAGE_DEMO_RUNBOOK.md`](GARAGE_DEMO_RUNBOOK.md) |

Both run on the `DEFAULT` (Azure) workspace under Unity Catalog schemas `mlops_pj.coverage_gap` and `mlops_pj.garage_checker`.

---

## Quick start

### Prerequisites
- Databricks CLI authenticated to the workspace (profile `DEFAULT`).
- A running serverless SQL warehouse (the build used `ec3b3b85811ecd2c`). The Garage demo needs serverless **17.1+** for `ai_parse_document`.
- Python with `databricks-sdk`. The Supervisor Agent API needs **>= 0.103** — install into an isolated folder if your global SDK is older:
  ```bash
  pip install --target ./.agentlibs "databricks-sdk==0.114.0"
  ```
- Foundation Model API access to `databricks-claude-sonnet-4-5`.

### Build the Coverage Gap Advisor
```bash
# 1. CRM tables, classifier function, policy-lookup function
python3 sql/run_sql.py sql/01_create_crm_data.sql
python3 sql/run_sql.py sql/02_create_function.sql
python3 sql/run_sql.py sql/03_create_policy_lookup.sql

# 2. Agents (Knowledge Assistant, Genie Space, Supervisor)
python3 agents/create_ka.py        # then wait ~10-15 min for indexing -> UPDATED
python3 agents/create_genie.py
PYTHONPATH="./.agentlibs" python3 agents/create_mas.py

# 3. Test
PYTHONPATH="./.agentlibs" python3 agents/test_advisor.py
```
> The schema, volume, and policy-PDF upload steps are CLI commands — see [`BUILD_GUIDE.md`](BUILD_GUIDE.md) sections 3–4.

### Build the Garage Repair Checker
```bash
python3 sql/garage/run_sql_garage.py sql/garage/01_create_garage_data.sql
python3 sql/garage/run_sql_garage.py sql/garage/02_parse_invoice.sql
python3 sql/garage/run_sql_garage.py sql/garage/03_assess_damage.sql
python3 sql/garage/run_sql_garage.py sql/garage/04_create_policy_lookup.sql

python3 agents/garage/create_genie_garage.py
PYTHONPATH="./.agentlibs" python3 agents/garage/create_mas_garage.py
PYTHONPATH="./.agentlibs" python3 agents/garage/test_garage.py
```
> Full steps (schema, volumes, generating invoices/photos) are in [`GARAGE_BUILD_GUIDE.md`](GARAGE_BUILD_GUIDE.md).

---

## Repository layout

```
.
├── BUILD_GUIDE.md            # Coverage Gap Advisor — full build walkthrough + RCA
├── DEMO_RUNBOOK.md           # Coverage Gap Advisor — demo flow, personas, prompts
├── GARAGE_BUILD_GUIDE.md     # Garage Repair Checker — full build walkthrough
├── GARAGE_DEMO_RUNBOOK.md    # Garage Repair Checker — demo flow
├── agents/                   # Agent creation scripts (KA, Genie, Supervisor, tests)
│   └── garage/               #   Garage demo agent scripts
├── sql/                      # CRM tables + UC functions (classifier, policy_lookup)
│   └── garage/               #   Garage demo SQL (data, invoice parse, damage assess)
├── scripts/                  # Helpers (invoice PDF generation, markdown -> PDF)
├── assets/                   # Mocked claim photos + invoices for the Garage demo
├── DOI/                      # Real Allianz Home + Motor Documents of Insurance (PDFs)
└── *.pdf                     # Rendered build guides
```

---

## Architecture (Coverage Gap Advisor)

```
                 Broker / customer life-change text
                              |
                   Coverage Gap Advisor  (Supervisor Agent / MAS)
                   classify -> profile -> policy -> cross-check -> report
                  /                |                         \
   classify_life_change      Customer Profile Analyst     Allianz Policy Analyst
     (UC Function,            (Genie Space over             (Knowledge Assistant over
      ai_query/Claude)         synthetic CRM tables)         real Allianz DOI PDFs)
```

The supervisor reads policy wording through a `policy_lookup` UC function (an `ai_query` wrapper over the KA endpoint) rather than the native Knowledge Assistant subagent — see [`BUILD_GUIDE.md`](BUILD_GUIDE.md) §8b for the root-cause analysis.

---

## Where to demo

- **AI Playground** → MAS endpoint for the full advisor / checker.
- **AI Playground** → KA endpoint for the policy assistant alone.
- **Genie** → the Customer Profile / Rate & Vehicle Analyst space for the CRM agent alone.
- **Agents page** → Knowledge Assistant and Supervisor Agent tiles.

Resource identifiers for this build are listed in [`BUILD_GUIDE.md`](BUILD_GUIDE.md) §9 and [`DEMO_RUNBOOK.md`](DEMO_RUNBOOK.md).

---

## Notes

- This is **decision support** for brokers/adjusters grounded in the real policy wording and the customer's actual profile — not customer advice.
- Synthetic CRM cover tiers and sublimits are aligned to the real Allianz DOI booklets, so every flagged gap is genuine and defensible.

---

## Disclaimer

THIS REPOSITORY AND ITS CONTENTS ARE PROVIDED **"AS IS"**, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, ACCURACY, AND NON-INFRINGEMENT. **USE AT YOUR OWN RISK.**

- This is a **demo / proof-of-concept** for illustrative purposes only. It is **not** a production system, and it is **not** insurance, legal, financial, or professional advice.
- All customer data is **synthetic**. Any resemblance to real individuals, policies, or claims is coincidental. The Allianz Document of Insurance (DOI) PDFs are included for demonstration only and remain the property of their respective owners.
- AI-generated outputs may be **inaccurate, incomplete, or out of date**. Always verify against the authoritative policy wording and applicable underwriting guidelines before relying on any result. The authors and contributors accept **no liability** for any loss or damage arising from use of this material.
- This repository is **not an official Allianz or Databricks product** and is not endorsed by either. All trademarks are the property of their respective owners.

To the maximum extent permitted by applicable law, in no event shall the authors or contributors be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with this repository or its use.
