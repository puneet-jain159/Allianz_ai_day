"""Create (or reuse) the Garage Repair Checker Supervisor Agent.

Wires four tools:
  invoice_parser        -> parse_invoice UC function   (live PDF itemisation)
  damage_photo_analyst  -> assess_damage UC function   (live multimodal vision)
  rate_vehicle_analyst  -> Genie space                 (ACV, book times, rates, total-loss threshold)
  policy_lookup         -> policy_lookup UC function    (real Allianz Motor DOI via KA endpoint)

Run with the pinned SDK:
  PYTHONPATH="./.agentlibs" python3 agents/garage/create_mas_garage.py
"""
from databricks.sdk import WorkspaceClient
import databricks.sdk.service.supervisoragents as sa

PROFILE = "DEFAULT"
DISPLAY_NAME = "Allianz Garage Repair Checker"

GENIE_SPACE_ID = "01f15edd7b931af0a5e4fde730e3f0de"
PARSE_INVOICE_FN = "mlops_pj.garage_checker.parse_invoice"
ASSESS_DAMAGE_FN = "mlops_pj.garage_checker.assess_damage"
POLICY_LOOKUP_FN = "mlops_pj.garage_checker.policy_lookup"

INSTRUCTIONS = (
    "You are the Garage Repair Checker for an Allianz UK motor claims team. Given a claim id (e.g. 'CLM-B'), "
    "review the garage's pre-repair photos and repair invoice and decide whether the proposed repair is "
    "justified, whether any costs should be challenged, whether the submitted imagery can be trusted, and "
    "whether the vehicle should instead be treated as a total loss.\n\n"
    "Always follow this workflow and use ALL of the tools:\n"
    "1. invoice_parser: call parse_invoice with the claim id to itemise the garage invoice (parts, labour hours, "
    "paint, sublet, and totals in GBP).\n"
    "2. damage_photo_analyst: call assess_damage with the claim id to see the visible damage per panel, the "
    "overall severity, and the image-authenticity verdict from the actual photo(s).\n"
    "3. rate_vehicle_analyst (Genie): look up the vehicle's ACV (pre-accident value), the standard book hours and "
    "expected labour rate for the operations on the invoice, the OEM vs aftermarket part prices, the claim's "
    "photo EXIF status, and the total-loss threshold (percent of ACV).\n"
    "4. policy_lookup: confirm the relevant Allianz motor policy wording you rely on - e.g. whether non-genuine "
    "(aftermarket) parts may be used, betterment, the excess, and how the policy treats a total loss / write-off. "
    "Cite the section it returns. If it cannot confirm a term, say the wording should be checked.\n\n"
    "Then CROSS-CHECK and reason:\n"
    "- Panel match: for every panel/part the invoice charges to repair or replace, is that panel actually shown "
    "as damaged in the photo assessment? List any invoice line billed for a panel that the photos show as "
    "undamaged - this is potential leakage.\n"
    "- Hours and rate: compare invoiced labour hours against the rate guide book hours, and the invoiced labour "
    "rate against the expected rate. Flag material over-billing.\n"
    "- Parts basis: note where genuine OEM parts are billed but the policy permits aftermarket / non-genuine "
    "parts (a betterment / cost point for the adjuster).\n"
    "- Image trust: if the photo authenticity verdict is SUSPECTED SYNTHETIC, or the EXIF status shows anomalies "
    "(missing camera metadata, generation software tags, a capture date before the incident), treat the imagery "
    "as unverified - the damage cannot be validated from it and the claim should go to an adjuster / SIU.\n"
    "- Total loss (do this for every claim): compute the repair-to-ACV ratio = invoice total / ACV as a "
    "percentage. If it is at or above the total-loss threshold, the vehicle is uneconomical to repair: HALT the "
    "repair authorisation and route to a total-loss adjuster before any work begins.\n\n"
    "Output EXACTLY this structure in Markdown:\n"
    "## Garage Repair Check: <CLAIM_ID> - <vehicle>\n"
    "**Claim snapshot:** vehicle and reg, reported damage area, garage, invoice total (GBP), ACV (GBP), "
    "repair-to-ACV ratio.\n"
    "**Verdict:** one of APPROVE / FLAG - REFER TO ADJUSTER / TOTAL LOSS - ROUTE TO ADJUSTER, plus a one-line reason.\n"
    "### Invoice breakdown\n"
    "Parts / Labour / Paint / Sublet subtotals and the total (GBP), with anything notable.\n"
    "### Photo vs invoice cross-check\n"
    "- Panels shown damaged in the photos\n"
    "- Invoice lines billed for panels with NO visible damage (each with its GBP amount) - or 'none'\n"
    "- Labour hours vs book hours, and labour rate vs expected rate\n"
    "- OEM vs aftermarket parts vs policy position (cite policy_lookup)\n"
    "### Image authenticity\n"
    "The authenticity verdict and any artefacts, plus the EXIF status. State clearly if the imagery is trusted.\n"
    "### Total loss check\n"
    "Repair-to-ACV ratio vs the threshold, and the resulting decision.\n"
    "### Estimated leakage / recommended action\n"
    "A GBP estimate of challenged cost where applicable and the concrete next action.\n"
    "### Note\n"
    "One line: this is decision support for the claims handler, grounded in the photos, the invoice, the rate "
    "guide and the policy wording - not a final coverage decision.\n\n"
    "Be precise, cite GBP figures, and never invent policy terms or damage that the photos do not show."
)

TOOLS = [
    ("invoice_parser", sa.Tool(
        tool_type="uc_function",
        uc_function=sa.UcFunction(name=PARSE_INVOICE_FN),
        description="Itemises the garage repair invoice PDF for a claim id into parts, labour hours, paint and sublet lines with GBP amounts and totals. Call this first to read what is being charged.",
    )),
    ("damage_photo_analyst", sa.Tool(
        tool_type="uc_function",
        uc_function=sa.UcFunction(name=ASSESS_DAMAGE_FN),
        description="Looks at the actual pre-repair photo(s) for a claim id with a vision model and returns per-panel visible damage, overall severity, and an image-authenticity verdict that flags AI-generated or manipulated imagery. Use to see what damage is real and whether the photos can be trusted.",
    )),
    ("rate_vehicle_analyst", sa.Tool(
        tool_type="genie_space",
        genie_space=sa.GenieSpace(id=GENIE_SPACE_ID),
        description="Vehicle ACV (pre-accident value), claim submission metadata incl. photo EXIF status, the standard repair rate guide (book hours, expected labour rate, OEM vs aftermarket part prices), and the total-loss threshold. Use to benchmark invoice costs and to get the ACV for the total-loss ratio.",
    )),
    ("policy_lookup", sa.Tool(
        tool_type="uc_function",
        uc_function=sa.UcFunction(name=POLICY_LOOKUP_FN),
        description="Authoritative Allianz motor policy wording (real Document of Insurance). Confirm aftermarket vs genuine parts, betterment, excess, approved-repairer terms, and total-loss / write-off provisions, and cite the section.",
    )),
]

EXAMPLES = [
    sa.Example(
        question="Review claim CLM-B and tell me if the repair invoice is justified.",
        guidelines=["Itemise the Apex invoice (front wing, front door skin, bonnet, rear quarter, 8-panel blow-over, "
                    "labour at 62/hr). Assess the photos: only the near-side front wing is damaged; door, bonnet and "
                    "rear quarter are undamaged and the photos are genuine. Flag the door skin, bonnet and rear quarter "
                    "lines as billed for undamaged panels, the labour hours above book time, the 62/hr rate above the "
                    "52/hr expected rate, and OEM parts where the policy permits aftermarket. Repair-to-ACV is well under "
                    "the threshold so not a total loss. Verdict FLAG - REFER TO ADJUSTER with a GBP leakage estimate."],
    ),
    sa.Example(
        question="Check claim CLM-C before we authorise the repair.",
        guidelines=["Itemise the Citywide invoice. When you assess the photo, the authenticity verdict is SUSPECTED "
                    "SYNTHETIC and the EXIF status shows no camera metadata, a generation software tag and a capture date "
                    "before the incident. Conclude the damage cannot be validated from the submitted imagery, do not "
                    "authorise on the current evidence, and route to an adjuster / SIU for genuine photographs. Verdict "
                    "FLAG - REFER TO ADJUSTER."],
    ),
    sa.Example(
        question="Should we repair the vehicle on claim CLM-D?",
        guidelines=["Itemise the Northgate invoice (~10,500 GBP inc VAT). The photos show severe frontal collision damage. "
                    "Get the ACV (8,500 GBP) from the rate/vehicle analyst and the total-loss threshold (60% of ACV). "
                    "Repair-to-ACV is about 124%, well above the threshold, so the vehicle is uneconomical to repair: "
                    "HALT the repair and route to a total-loss adjuster before any work begins. Verdict TOTAL LOSS - ROUTE "
                    "TO ADJUSTER. Cite the policy total-loss wording via policy_lookup."],
    ),
    sa.Example(
        question="Review claim CLM-A.",
        guidelines=["Itemise the Northgate invoice (front bumper corner + O/S headlamp, ~884 GBP inc VAT). The photo shows "
                    "exactly that damage and is genuine. Hours match book time, rate is in line, aftermarket parts used. "
                    "Repair-to-ACV is tiny. Verdict APPROVE - the invoice is consistent with the visible damage and "
                    "standard rates."],
    ),
]

w = WorkspaceClient(profile=PROFILE)

agent = None
for a in w.supervisor_agents.list_supervisor_agents():
    if a.display_name == DISPLAY_NAME:
        agent = a
        break

if agent is None:
    agent = w.supervisor_agents.create_supervisor_agent(
        supervisor_agent=sa.SupervisorAgent(
            display_name=DISPLAY_NAME,
            description="Reviews pre-repair vehicle photos and a garage repair invoice against the rate guide and the real Allianz motor policy to flag inflated invoices, undamaged-panel billing and AI-generated imagery, and to route total losses before repair work begins.",
            instructions=INSTRUCTIONS,
        )
    )
    print(f"Created supervisor agent id={agent.supervisor_agent_id} name={agent.name} endpoint={agent.endpoint_name}")
else:
    # keep instructions current on reuse
    w.supervisor_agents.update_supervisor_agent(
        name=agent.name,
        supervisor_agent=sa.SupervisorAgent(display_name=DISPLAY_NAME, instructions=INSTRUCTIONS),
        update_mask=sa.FieldMask(field_mask=["instructions"]),
    )
    print(f"Reusing supervisor agent id={agent.supervisor_agent_id} name={agent.name} endpoint={agent.endpoint_name}")

existing_tool_ids = {t.tool_id for t in w.supervisor_agents.list_tools(parent=agent.name)}
for tool_id, tool in TOOLS:
    if tool_id in existing_tool_ids:
        print(f"Tool {tool_id} already exists, skipping")
        continue
    created = w.supervisor_agents.create_tool(parent=agent.name, tool=tool, tool_id=tool_id)
    print(f"Added tool {created.tool_id} ({created.tool_type})")

for ex in EXAMPLES:
    try:
        w.supervisor_agents.create_example(parent=agent.name, example=ex)
        print("Added example.")
    except Exception as e:
        print(f"Example add note: {e}")

print(f"MAS_ID={agent.supervisor_agent_id}")
print(f"MAS_ENDPOINT={agent.endpoint_name}")
