-- =====================================================
-- FDA Drug Safety Pipeline - Analytics Queries

-- ─────────────────────────────────────────────────
-- QUERY 1: ALL RECALLS WITH FULL DETAILS

-- ─────────────────────────────────────────────────
SELECT
    recall_number,
    product_description,
    classification,
    risk_score,
    reason_category,
    company_clean,
    state,
    country,
    recall_initiation_date,
    status
FROM drug_recalls
ORDER BY recall_initiation_date DESC;


-- ─────────────────────────────────────────────────
-- QUERY 2: CLASSIFICATION BREAKDOWN
-- "How many recalls per severity level?"
-- ─────────────────────────────────────────────────
SELECT
    classification,
    COUNT(*)                      AS total_recalls,
    ROUND(AVG(risk_score), 1)     AS avg_risk_score,
    MIN(recall_initiation_date)   AS earliest_recall,
    MAX(recall_initiation_date)   AS latest_recall
FROM drug_recalls
GROUP BY classification
ORDER BY avg_risk_score DESC;


-- ─────────────────────────────────────────────────
-- QUERY 3: TOP COMPANIES WITH MOST RECALLS
-- "Which companies have the worst track record?"
-- ─────────────────────────────────────────────────
SELECT
    company_clean,
    total_recalls,
    class_1_recalls         AS most_serious,
    class_2_recalls         AS moderate,
    class_3_recalls         AS minor,
    avg_risk_score,
    is_repeat_offender,
    last_recall_date
FROM company_recall_summary
ORDER BY total_recalls DESC, avg_risk_score DESC
LIMIT 10;


-- ─────────────────────────────────────────────────
-- QUERY 4: RECALLS BY REASON CATEGORY
-- "Why are drugs being recalled?"
-- ─────────────────────────────────────────────────
SELECT
    reason_category,
    COUNT(*)                    AS total_recalls,
    ROUND(AVG(risk_score), 1)   AS avg_risk_score,
    COUNT(*) FILTER (
        WHERE classification = 'Class I'
    )                           AS class_1_count
FROM drug_recalls
GROUP BY reason_category
ORDER BY total_recalls DESC;


-- ─────────────────────────────────────────────────
-- QUERY 5: RECALLS BY US STATE
-- "Which states have the most recalls?"
-- ─────────────────────────────────────────────────
SELECT
    state,
    COUNT(*)                    AS total_recalls,
    ROUND(AVG(risk_score), 1)   AS avg_risk
FROM drug_recalls
WHERE country = 'United States'
  AND state IS NOT NULL
  AND state != ''
GROUP BY state
ORDER BY total_recalls DESC
LIMIT 10;


-- ─────────────────────────────────────────────────
-- QUERY 6: VOLUNTARY VS MANDATED
-- "Do companies report themselves or get caught?"
-- ─────────────────────────────────────────────────
SELECT
    voluntary_mandated,
    COUNT(*)                    AS total,
    ROUND(AVG(risk_score), 1)   AS avg_risk_score
FROM drug_recalls
WHERE voluntary_mandated IS NOT NULL
GROUP BY voluntary_mandated
ORDER BY total DESC;


-- ─────────────────────────────────────────────────
-- QUERY 7: ONGOING VS COMPLETED RECALLS
-- "How many recalls are still active?"
-- ─────────────────────────────────────────────────
SELECT
    status,
    COUNT(*)                    AS total,
    ROUND(AVG(risk_score), 1)   AS avg_risk
FROM drug_recalls
GROUP BY status
ORDER BY total DESC;


-- ─────────────────────────────────────────────────
-- QUERY 8: HIGH RISK RECALLS ONLY
-- "Show me only the most dangerous recalls"
-- ─────────────────────────────────────────────────
SELECT
    recall_number,
    product_description,
    classification,
    risk_score,
    company_clean,
    reason_for_recall,
    recall_initiation_date
FROM drug_recalls
WHERE risk_score >= 6          -- Class I and Class II only
  AND status = 'Ongoing'       -- still active
ORDER BY risk_score DESC,
         recall_initiation_date DESC;


-- ─────────────────────────────────────────────────
-- QUERY 9: MONTHLY RECALL TRENDS
-- "Are recalls increasing or decreasing?"
-- ─────────────────────────────────────────────────
SELECT
    DATE_TRUNC('month', recall_initiation_date) AS month,
    COUNT(*)                                     AS total_recalls,
    COUNT(*) FILTER (
        WHERE classification = 'Class I'
    )                                            AS class_1_recalls,
    ROUND(AVG(risk_score), 1)                    AS avg_risk
FROM drug_recalls
WHERE recall_initiation_date IS NOT NULL
GROUP BY DATE_TRUNC('month', recall_initiation_date)
ORDER BY month DESC;


-- ─────────────────────────────────────────────────
-- QUERY 10: DRUG ROUTE ANALYSIS
-- "Which type of drug has most recalls?"
-- ─────────────────────────────────────────────────
SELECT
    route,
    COUNT(*)                    AS total_recalls,
    ROUND(AVG(risk_score), 1)   AS avg_risk_score
FROM drug_recalls
WHERE route IS NOT NULL
  AND route != 'Unknown'
GROUP BY route
ORDER BY total_recalls DESC;


-- ─────────────────────────────────────────────────
-- QUERY 11: NATIONWIDE VS LOCAL DISTRIBUTION
-- "How widespread are these recalls?"
-- ─────────────────────────────────────────────────
SELECT
    CASE
        WHEN LOWER(distribution_pattern) LIKE '%nationwide%' THEN 'Nationwide'
        WHEN LOWER(distribution_pattern) LIKE '%international%' THEN 'International'
        WHEN distribution_pattern IS NULL THEN 'Unknown'
        ELSE 'Regional'
    END                         AS distribution_scope,
    COUNT(*)                    AS total_recalls,
    ROUND(AVG(risk_score), 1)   AS avg_risk
FROM drug_recalls
GROUP BY distribution_scope
ORDER BY total_recalls DESC;

SELECT
    recall_number,
    product_description,
    classification,
    reason_category,
    recall_initiation_date
FROM drug_recalls
WHERE company_clean LIKE '%Glenmark%'
ORDER BY recall_initiation_date DESC
LIMIT 10;


-- ─────────────────────────────────────────────────
-- QUERY 12: PIPELINE HEALTH DASHBOARD
-- "Is our pipeline running correctly?"
-- ─────────────────────────────────────────────────
SELECT
    run_at,
    records_fetched,
    records_loaded,
    ROUND(duration_seconds::NUMERIC, 2) AS duration_seconds,
    status,
    error_message
FROM pipeline_logs
ORDER BY run_at DESC
LIMIT 10;