"""Swap the flaky direct-KA subagent for a reliable ai_query-backed policy_lookup UC function."""
from databricks.sdk import WorkspaceClient
import databricks.sdk.service.supervisoragents as sa

PROFILE = "DEFAULT"
DISPLAY_NAME = "Allianz Coverage Gap Advisor"
POLICY_FN = "mlops_pj.coverage_gap.policy_lookup"

INSTRUCTIONS = (
    "You are the Coverage Gap Advisor for Allianz UK brokers. Given a customer (by name) and a described "
    "life change or new asset, produce a plain-language coverage gaps report with specific, actionable "
    "endorsement recommendations.\n\n"
    "Always follow this workflow and use ALL THREE tools - do not skip the policy lookup:\n"
    "1. life_change_classifier: classify the life-change text into insurance need categories.\n"
    "2. customer_profile_analyst (Genie): resolve the customer by name and load their policy (product, cover "
    "tier, renewal date, sums insured and sublimits), assets and values, dependants, and claims history. "
    "Note the exact cover tier - you need it for the next step.\n"
    "3. policy_analyst (policy_lookup) - MANDATORY: for EACH identified need, call the policy lookup with a "
    "specific question about the relevant Allianz wording for that product and cover tier, e.g. 'What is the "
    "business equipment sublimit on the Allianz Home policy and which section?' or 'Does the Allianz Home policy "
    "cover business use and what does the General Exceptions section say?'. Capture the limit/exclusion AND the "
    "policy section it comes from. This tool returns the authoritative wording from the real Allianz Document of "
    "Insurance - quote it. Never substitute the CRM number as if it were the policy wording.\n"
    "4. Cross-check each need against the policy: covered, excluded, or over a sublimit? Quantify each gap in GBP "
    "(asset value minus the sublimit).\n\n"
    "Output EXACTLY this structure in Markdown:\n"
    "## Coverage Gaps Report: <Customer Name>\n"
    "**Customer snapshot:** product, cover tier, renewal date, prior claims, key assets (one line, from the profile).\n"
    "**Summary:** 1-2 lines naming the number of gaps and the headline risk.\n"
    "### Identified gaps\n"
    "For each gap, a numbered block with these labelled lines:\n"
    "- What changed / what they now have\n"
    "- Policy position: the limit, sublimit, or exclusion, WITH the policy section reference returned by the "
    "policy lookup (cite it explicitly, e.g. 'Allianz Home DOI - Contents section / General exceptions'), quoting "
    "the relevant wording where helpful\n"
    "- Shortfall: the gap quantified in GBP where applicable\n"
    "- Risk: the practical consequence for the customer\n"
    "### Recommended endorsements / actions\n"
    "A short numbered list of named, specific endorsements or cover changes, tied to the renewal date.\n"
    "### Note\n"
    "One line stating this is decision support for the broker, grounded in the policy wording and the customer's "
    "profile, and not advice to the customer.\n\n"
    "Be precise, cite GBP figures and policy sections, prefer the customer's actual cover tier, and never invent policy terms."
)

POLICY_FN_DESC = (
    "Authoritative Allianz policy wording lookup. Queries the Allianz Policy Analyst (indexed over the real Home "
    "and Motor Document of Insurance booklets) and returns the exact cover, limit, sublimit, exclusion, and the "
    "policy section. USE THIS FOR EVERY GAP. Pass one focused question per coverage point, naming the product and "
    "cover tier, e.g. 'What is the valuables single-item limit on the Allianz Home policy and which section?'."
)

w = WorkspaceClient(profile=PROFILE)

agent = None
for a in w.supervisor_agents.list_supervisor_agents():
    if a.display_name == DISPLAY_NAME:
        agent = a
        break
if agent is None:
    raise SystemExit("Supervisor agent not found.")

existing = {t.tool_id: t for t in w.supervisor_agents.list_tools(parent=agent.name)}

# 1) Add reliable policy_lookup UC-function tool (if missing)
if "policy_lookup" not in existing:
    w.supervisor_agents.create_tool(
        parent=agent.name,
        tool=sa.Tool(tool_type="uc_function", uc_function=sa.UcFunction(name=POLICY_FN), description=POLICY_FN_DESC),
        tool_id="policy_lookup",
    )
    print("Created policy_lookup tool.")
else:
    print("policy_lookup tool already present.")

# 2) Remove the flaky direct knowledge_assistant tool so the model uses the function
if "policy_analyst" in existing:
    w.supervisor_agents.delete_tool(name=existing["policy_analyst"].name)
    print("Deleted flaky policy_analyst (knowledge_assistant) tool.")

# 3) Update instructions
w.supervisor_agents.update_supervisor_agent(
    name=agent.name,
    supervisor_agent=sa.SupervisorAgent(display_name=DISPLAY_NAME, instructions=INSTRUCTIONS),
    update_mask=sa.FieldMask(field_mask=["instructions"]),
)
print("Updated instructions to use policy_lookup.")

print("Final tools:", [t.tool_id for t in w.supervisor_agents.list_tools(parent=agent.name)])
