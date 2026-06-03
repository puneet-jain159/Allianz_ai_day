"""Create (or reuse) the Repair Rate & Vehicle Analyst Genie Space for the Garage Repair Checker."""
import json, uuid
from databricks.sdk import WorkspaceClient

PROFILE = "DEFAULT"
WAREHOUSE_ID = "ec3b3b85811ecd2c"
TITLE = "Allianz Repair Rate & Vehicle Analyst"
DESCRIPTION = ("Natural-language access to motor-claim vehicles and their pre-accident values (ACV), claim "
               "submission metadata, the standard repair rate guide (book times, labour rates, OEM vs "
               "aftermarket part prices), and the total-loss threshold. Used by the Garage Repair Checker to "
               "benchmark invoice costs and decide total-loss routing.")
CATALOG, SCHEMA = "mlops_pj", "garage_checker"


def hid():
    return uuid.uuid4().hex  # 32-char hex


def tbl(name, desc):
    return {"identifier": f"{CATALOG}.{SCHEMA}.{name}", "description": [desc]}


questions = [
    "What is the ACV (pre-accident value) of the vehicle on claim CLM-D?",
    "For claim CLM-D, what is the repair-to-ACV ratio if the invoice total is divided by the ACV?",
    "What is the standard book time and expected labour rate to replace a front wing?",
    "What does the rate guide say the OEM and aftermarket price is for a headlamp unit?",
    "What is the total loss threshold and what does it mean?",
    "What is the invoice total, reported damage area, and photo EXIF status for claim CLM-B?",
    "List the standard book hours and labour rate for each repair operation in the rate guide.",
]

instructions_text = (
    "All monetary values are in GBP. Join vehicles, claims on claim_id. "
    "vehicles.acv_gbp is the pre-accident (actual cash) value of the vehicle. "
    "claims.invoice_total_gbp is the garage invoice total INCLUSIVE of VAT, and claims.reported_damage_area is "
    "the damage area stated at first notification of loss. claims.photo_exif_status describes the image metadata "
    "and any anomalies. To compute the repair-to-ACV ratio for a claim, divide invoice_total_gbp by acv_gbp and "
    "express as a percentage. rate_guide.book_hours is the industry-standard time for an operation and "
    "std_labour_rate_gbp is the expected hourly rate; oem_part_gbp and aftermarket_part_gbp are expected part "
    "prices (NULL where not a part operation). repair_benchmarks holds the standard labour rates and the "
    "total_loss_threshold (value 60, unit percent_of_ACV): a vehicle is treated as a total loss when the "
    "repair-to-ACV ratio is at or above this percentage. When asked about a claim by id, use the exact id (e.g. CLM-B)."
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
            tbl("vehicles", "One row per claimed vehicle: registration, make/model, year, body style, mileage, and ACV (pre-accident value) in GBP."),
            tbl("claims", "One row per claim: policy ref, vehicle reg, date reported, incident description, reported damage area, photo count, photo EXIF status, garage name, and invoice total (inc VAT) in GBP."),
            tbl("rate_guide", "Standard repair rate guide: per operation, the panel, standard book_hours, expected labour rate, and OEM vs aftermarket part prices in GBP."),
            tbl("repair_benchmarks", "Benchmark labour rates and the total-loss threshold (percent of ACV above which a vehicle is uneconomical to repair)."),
        ], key=lambda x: x["identifier"]),
    },
    "instructions": {
        "text_instructions": [{"id": hid(), "content": [instructions_text]}],
    },
}

w = WorkspaceClient(profile=PROFILE)

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
