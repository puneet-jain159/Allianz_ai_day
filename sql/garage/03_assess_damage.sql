-- =====================================================================
-- UC Function: assess_damage(claim_id)
-- Live multimodal damage + image-authenticity assessment. Reads every
-- pre-repair photo for the claim from claim_photos and runs a vision model
-- (ai_query with files => content) per image, then concatenates the results.
-- Covers two capabilities at once:
--   1. Per-panel visible damage assessment + overall severity
--   2. AI-generated / manipulated image detection (artefacts, lighting,
--      reflections, geometry) -> authenticity verdict for adjuster review
-- =====================================================================
CREATE OR REPLACE FUNCTION mlops_pj.garage_checker.assess_damage(in_claim_id STRING)
RETURNS STRING
COMMENT 'Looks at the actual pre-repair photo(s) submitted for a given claim id (e.g. "CLM-B") using a vision model and returns, per photo: (1) the visible damage broken down by exterior panel with a severity for each, (2) an overall damage severity rating (Minor / Moderate / Severe / Likely total loss), and (3) an image-authenticity verdict that flags any signs of AI generation or digital manipulation (inconsistent lighting or shadows, warped reflections, impossible geometry, melted textures, generation artefacts). Call this to see what damage is actually visible and whether the imagery can be trusted, then compare it against the invoice line items.'
RETURN (
  SELECT concat_ws('\n\n', collect_list(per_photo))
  FROM (
    SELECT concat(
      '=== Photo: ', file_name, ' ===\n',
      ai_query(
        'databricks-claude-sonnet-4-5',
        'You are a senior motor-claims damage assessor and image-forensics analyst reviewing a pre-repair photo. Respond in three clearly labelled sections.\n\n1) VISIBLE DAMAGE BY PANEL: list each exterior panel you can see (e.g. front bumper, bonnet, near-side front wing, near-side front door, near-side rear door, rear quarter, headlamps, grille, wheels) and state for each whether it is Undamaged or Damaged, and if damaged give a severity (Light / Moderate / Severe) and a few words on what you see. Be strict: only mark a panel damaged if damage is actually visible.\n2) OVERALL SEVERITY: one of Minor / Moderate / Severe / Likely total loss, with a one-line justification.\n3) IMAGE AUTHENTICITY: state whether the image looks like a genuine photograph or shows signs of AI generation or digital manipulation. Call out any specific artefacts (inconsistent lighting or shadow directions, warped or impossible reflections, distorted geometry such as misshapen wheels or trim, melted or over-smooth textures, garbled text/number plates). End with a verdict line exactly in the form "AUTHENTICITY: GENUINE" or "AUTHENTICITY: SUSPECTED SYNTHETIC - FLAG FOR REVIEW". Be concise.',
        files => content
      )
    ) AS per_photo
    FROM mlops_pj.garage_checker.claim_photos
    WHERE claim_id = in_claim_id
  )
);
