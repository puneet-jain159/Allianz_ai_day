"""Create the Coverage Gap Advisor Supervisor Agent, wiring the Genie space, KA, and UC function."""
from databricks.sdk import WorkspaceClient
import databricks.sdk.service.supervisoragents as sa

PROFILE = "DEFAULT"
DISPLAY_NAME = "Allianz Coverage Gap Advisor"

KA_ID = "924e4b7c-5165-44fb-8985-b6d6962f8a1d"
KA_ENDPOINT = "ka-924e4b7c-endpoint"
GENIE_SPACE_ID = "01f15eca8e531019982990a65ade688e"
UC_FUNCTION = "mlops_pj.coverage_gap.classify_life_change"

INSTRUCTIONS = (
    "You are the Coverage Gap Advisor for Allianz UK brokers. Given a customer (by name) and a described "
    "life change or new asset, produce a plain-language coverage gaps report with specific, actionable "
    "endorsement recommendations.\n\n"
    "Workflow:\n"
    "1. Call the life change classifier on the life-change text to identify the relevant insurance need categories.\n"
    "2. Use the Customer Profile Analyst to load the customer's policy (product, cover tier, renewal date, sums "
    "insured, sublimits), assets and values, dependants, and claims history. Resolve the customer by name.\n"
    "3. Use the Policy Analyst to confirm the exact limits, sublimits, and exclusions in the relevant Allianz "
    "policy wording for that product and cover tier.\n"
    "4. Cross-check each identified need against the current policy: is it covered, excluded, or over a sublimit? "
    "Quantify each gap in GBP (e.g. asset value minus the sublimit).\n"
    "5. Output a structured report with: a 1-2 line summary; an Identified Gaps section (for each gap: what the "
    "customer now has/does, the relevant policy limit or exclusion with the policy section, the shortfall in GBP, "
    "and the risk); a Recommended Endorsements/Actions section (named and specific); and a closing note that this "
    "is decision support for the broker, not advice to the customer.\n"
    "Be precise, cite GBP figures, and never invent policy terms - if unsure, say the policy wording should be checked."
)

TOOLS = [
    ("life_change_classifier", sa.Tool(
        tool_type="uc_function",
        uc_function=sa.UcFunction(name=UC_FUNCTION),
        description="Classifies a plain-language life change or new asset into relevant insurance need categories. Call this first.",
    )),
    ("customer_profile_analyst", sa.Tool(
        tool_type="genie_space",
        genie_space=sa.GenieSpace(id=GENIE_SPACE_ID),
        description="Customer CRM profile. Look up a customer's policy tier, renewal date, sums insured, sublimits, assets and values, dependants, claims history, and disclosed life events by customer name.",
    )),
    ("policy_analyst", sa.Tool(
        tool_type="knowledge_assistant",
        knowledge_assistant=sa.KnowledgeAssistant(knowledge_assistant_id=KA_ID, serving_endpoint_name=KA_ENDPOINT),
        description="Authoritative Allianz policy wording (Home and Motor Document of Insurance). Coverage types, limits, sublimits, and exclusions by product and cover tier.",
    )),
]

EXAMPLES = [
    sa.Example(
        question="Sarah Thompson has started a home catering business and bought 4,800 pounds of equipment including a camera for food photography. Her niece helps at weekend events. What are her coverage gaps?",
        guidelines=["Classify the life change, load Sarah's Bronze Home policy via the Customer Profile Analyst, "
                    "and confirm via the Policy Analyst: the business equipment sublimit (1,000 GBP on Bronze), the "
                    "business pursuits / business use exclusion, and that liability to domestic employees is excluded on Bronze. "
                    "Report three gaps with GBP shortfalls (e.g. 4,800 - 1,000 = 3,800 over the business equipment sublimit) and "
                    "recommend a home business / business equipment endorsement, business public liability cover, and employers' liability cover."],
    ),
    sa.Example(
        question="James O'Connor has started doing food delivery for Deliveroo in his car. Are there any coverage gaps on his motor policy?",
        guidelines=["Identify motor business use / hire-and-reward. Load James's Allianz Silver motor policy (use class Social, "
                    "Domestic, Pleasure & Commuting; business use not covered) and confirm the business/hire-and-reward exclusion in the "
                    "Motor policy wording. Report that food delivery is excluded under the current use class and recommend adding "
                    "hire-and-reward / business use cover."],
    ),
    sa.Example(
        question="Priya Patel just got engaged and bought a 6,000 pound diamond engagement ring. Are there any coverage gaps on her home policy?",
        guidelines=["Classify as a high-value valuables need. Load Priya's Gold Home policy via the Customer Profile Analyst, "
                    "then ask the Policy Analyst to confirm the valuables single item limit on the Allianz Home policy and its "
                    "section. Report the ring (6,000) vs the single item limit (2,000) as a 4,000 GBP gap, citing the Summary of "
                    "policy limits, and recommend specifying the ring via a valuables / personal belongings endorsement."],
    ),
]

w = WorkspaceClient(profile=PROFILE)

# Reuse if exists
agent = None
for a in w.supervisor_agents.list_supervisor_agents():
    if a.display_name == DISPLAY_NAME:
        agent = a
        break

if agent is None:
    agent = w.supervisor_agents.create_supervisor_agent(
        supervisor_agent=sa.SupervisorAgent(
            display_name=DISPLAY_NAME,
            description="Reviews a customer's policy and CRM profile alongside a described life change and produces a plain-language coverage gaps report with endorsement recommendations.",
            instructions=INSTRUCTIONS,
        )
    )
    print(f"Created supervisor agent id={agent.supervisor_agent_id} name={agent.name} endpoint={agent.endpoint_name}")
else:
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
