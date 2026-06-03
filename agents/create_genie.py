"""Create (or reuse) the Customer Profile Analyst Genie Space over the synthetic CRM tables."""
import json, uuid
from databricks.sdk import WorkspaceClient

PROFILE = "DEFAULT"
WAREHOUSE_ID = "ec3b3b85811ecd2c"
TITLE = "Allianz Customer Profile Analyst"
DESCRIPTION = ("Natural-language access to the synthetic Allianz CRM: customers, policies, assets, "
               "dependants, claims, and disclosed life events. Used by the Coverage Gap Advisor to "
               "understand a customer's existing assets, cover, renewal timing, and risk exposure.")
CATALOG, SCHEMA = "mlops_pj", "coverage_gap"

def hid():
    return uuid.uuid4().hex  # 32-char hex

def tbl(name, desc):
    return {"identifier": f"{CATALOG}.{SCHEMA}.{name}", "description": [desc]}

questions = [
    "What is the cover tier, renewal date, and business equipment sublimit on Sarah Thompson's home policy?",
    "List all assets and their values for Sarah Thompson.",
    "How many claims does Sarah Thompson have and what were they for?",
    "How many dependants does Sarah Thompson have?",
    "What is the most recent disclosed life event for each customer?",
    "What is the valuables single item limit on Priya Patel's policy and what is her engagement ring worth?",
    "What use class and business-use cover does James O'Connor's motor policy have?",
]

instructions_text = (
    "All monetary values are in GBP. Join tables on customer_id; policies also link via policy_id. "
    "Cover tiers: Home is Bronze/Silver/Gold, Motor is Essentials/Silver/Allianz. "
    "policies.business_equipment_sublimit_gbp, valuables_single_item_limit_gbp, "
    "personal_belongings_single_item_limit_gbp, public_liability_gbp and domestic_employee_liability_gbp "
    "are the relevant sublimits/limits (a value of 0 means the cover is excluded for that tier). "
    "policies.business_use_covered indicates whether business/commercial use is included. "
    "life_events.event_description holds the customer's disclosed life change in plain language. "
    "When asked about a customer by name, resolve the name via the customers table to customer_id."
)

serialized = {
    "version": 2,
    "config": {
        "sample_questions": sorted(
            [{"id": hid(), "question": [q]} for q in questions], key=lambda x: x["id"]
        )
    },
    "data_sources": {
        "tables": sorted([
            tbl("customers", "One row per customer: name, DOB, occupation, location, tenure, segment."),
            tbl("policies", "One row per policy with product type, cover tier, renewal date, premium, and all sums insured / sublimits in GBP."),
            tbl("assets", "Customer assets (property, vehicles, jewellery, business equipment, electronics) with estimated value in GBP."),
            tbl("dependants", "Dependants linked to each customer."),
            tbl("claims", "Claims history with type, amount in GBP, and status."),
            tbl("life_events", "Disclosed life changes / new assets in plain language."),
        ], key=lambda x: x["identifier"]),
    },
    "instructions": {
        "text_instructions": [{"id": hid(), "content": [instructions_text]}],
    },
}

w = WorkspaceClient(profile=PROFILE)

# Reuse if a space with this title already exists
existing_id = None
resp = w.genie.list_spaces()
for sp in (resp.spaces or []):
    if getattr(sp, "title", None) == TITLE:
        existing_id = sp.space_id
        break

if existing_id:
    space = w.genie.update_space(
        space_id=existing_id, serialized_space=json.dumps(serialized),
        title=TITLE, description=DESCRIPTION, warehouse_id=WAREHOUSE_ID,
    )
    print(f"Updated Genie space space_id={space.space_id}")
else:
    space = w.genie.create_space(
        warehouse_id=WAREHOUSE_ID, serialized_space=json.dumps(serialized),
        title=TITLE, description=DESCRIPTION,
    )
    print(f"Created Genie space space_id={space.space_id}")

print(f"GENIE_SPACE_ID={space.space_id}")
