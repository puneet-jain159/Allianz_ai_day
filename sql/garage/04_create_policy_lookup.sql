-- =====================================================================
-- UC Function: policy_lookup(question)
-- Wraps the existing Allianz Policy Analyst Knowledge Assistant endpoint
-- (indexed over the real Allianz Motor + Home Document of Insurance) so the
-- Garage Repair Checker can confirm motor coverage terms - excess/deductible,
-- OEM vs aftermarket parts, betterment, and total-loss / write-off provisions.
-- Same reliable ai_query-over-KA pattern used in the Coverage Gap demo.
-- =====================================================================
CREATE OR REPLACE FUNCTION mlops_pj.garage_checker.policy_lookup(question STRING)
RETURNS STRING
COMMENT 'Looks up authoritative Allianz motor policy wording by querying the Allianz Policy Analyst Knowledge Assistant (indexed over the real Allianz Motor and Home Document of Insurance booklets). Pass one focused question about a specific term - e.g. the policy excess, whether the insurer can fit aftermarket / non-genuine parts, betterment, approved-repairer requirements, or how the policy treats a total loss / writing off the vehicle. Returns the policy wording with the relevant section. Use this to confirm and cite policy terms when judging a repair invoice or a total-loss decision.'
RETURN ai_query('ka-924e4b7c-endpoint', question);
