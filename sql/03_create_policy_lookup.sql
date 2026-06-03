CREATE OR REPLACE FUNCTION mlops_pj.coverage_gap.policy_lookup(question STRING)
RETURNS STRING
COMMENT 'Looks up authoritative Allianz policy wording by querying the Allianz Policy Analyst Knowledge Assistant (indexed over the real Home and Motor Document of Insurance booklets). Pass one focused question about a specific cover, limit, sublimit, exclusion, or section for a given product and cover tier (e.g. "What is the business equipment sublimit on the Allianz Home policy and which section?"). Returns the policy wording answer including the relevant section. Use this to confirm and cite exact policy terms for every coverage gap.'
RETURN ai_query('ka-924e4b7c-endpoint', question)
