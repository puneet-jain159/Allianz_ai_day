"""Create (or reuse) the Allianz Policy Analyst Knowledge Assistant over the policy PDFs."""
from databricks.sdk import WorkspaceClient
import databricks.sdk.service.knowledgeassistants as ka

PROFILE = "DEFAULT"
DISPLAY_NAME = "Allianz Policy Analyst"
VOLUME_PATH = "/Volumes/mlops_pj/coverage_gap/policies"
INSTRUCTIONS = (
    "You are a policy analyst for Allianz UK personal lines. Answer strictly from the indexed "
    "Allianz policy booklets (Home and Motor Document of Insurance). When asked about cover, always "
    "state the specific limit, sublimit, or exclusion and name the cover tier (Home: Bronze/Silver/Gold; "
    "Motor: Essentials/Silver/Allianz) and the policy section. If a cover is excluded or optional, say so "
    "explicitly. Quote figures in GBP. If the policy does not address something, say it is not specified. "
    "Be concise and precise."
)
DESCRIPTION = (
    "Reads Allianz Home and Motor policy documents and answers what is covered, what is excluded, "
    "and what sublimits apply."
)

w = WorkspaceClient(profile=PROFILE)

# Reuse if it already exists
existing = None
for a in w.knowledge_assistants.list_knowledge_assistants():
    if a.display_name == DISPLAY_NAME:
        existing = a
        break

if existing:
    assistant = existing
    print(f"Reusing KA id={assistant.id} name={assistant.name} state={assistant.state}")
else:
    assistant = w.knowledge_assistants.create_knowledge_assistant(
        knowledge_assistant=ka.KnowledgeAssistant(
            display_name=DISPLAY_NAME, description=DESCRIPTION, instructions=INSTRUCTIONS,
        )
    )
    print(f"Created KA id={assistant.id} name={assistant.name} endpoint={assistant.endpoint_name}")

# Add a FILES knowledge source over the policy volume if none exists
sources = list(w.knowledge_assistants.list_knowledge_sources(parent=assistant.name))
if not sources:
    src = w.knowledge_assistants.create_knowledge_source(
        parent=assistant.name,
        knowledge_source=ka.KnowledgeSource(
            display_name="Allianz DOI booklets",
            description="Allianz Home (Bronze/Silver/Gold) and Motor (Essentials/Silver/Allianz) Document of Insurance PDFs.",
            source_type="FILES",
            files=ka.FilesSpec(path=VOLUME_PATH),
        ),
    )
    print(f"Created knowledge source id={src.id} name={src.name} state={src.state}")
else:
    print(f"Knowledge source(s) already present: {[s.id for s in sources]}")

# NOTE: some SDK versions send no request body and the API rejects it
# ("Request requires a JSON object body"). Call the REST endpoint with {} directly.
w.api_client.do("POST", f"/api/2.1/{assistant.name}/knowledge-sources:sync", body={})
print("Triggered knowledge-source sync (re-indexing).")
print(f"KA_ID={assistant.id}")
print(f"KA_ENDPOINT={assistant.endpoint_name}")
