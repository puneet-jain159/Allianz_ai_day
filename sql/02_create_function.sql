-- =====================================================================
-- UC Function: classify_life_change
-- Maps a plain-language life change / new asset into the insurance need
-- categories the Coverage Gap Advisor should cross-check against the policy.
-- Backed by a Foundation Model API endpoint via ai_query.
-- =====================================================================
CREATE OR REPLACE FUNCTION mlops_pj.coverage_gap.classify_life_change(life_change STRING)
RETURNS STRING
COMMENT 'Classifies a customer life change or newly acquired asset into relevant insurance need categories (e.g. home business / business pursuits liability, business equipment cover, employers liability, high-value valuables, personal belongings, motor business use / hire and reward, new vehicle, new dependant). Returns a short categorised list with a one-line reason for each. Call this first when analysing a life change.'
RETURN ai_query(
  'databricks-claude-sonnet-4-5',
  CONCAT(
    'You are an insurance needs classifier for a UK personal lines insurer (Allianz). ',
    'Given a customer life change or new asset described in plain language, identify which of the following insurance need categories apply. ',
    'Categories: [home business / business pursuits liability | business equipment cover | employers (domestic staff/helper) liability | high-value item / valuables single-item limit | personal belongings | motor business use / hire-and-reward | new vehicle | new dependant / life cover | travel | pet]. ',
    'Return ONLY the categories that genuinely apply as a short bullet list. For each, give a one-line reason grounded in the description. Be concise and do not invent facts. ',
    'Life change: ', life_change
  )
);
