📋 SECTION 1 — About the Dataset
DATA SOURCE:

- Name: OpenFDA Drug Enforcement API
- Owner: US Food and Drug Administration (FDA)
- Website: api.fda.gov
- Cost: 100% Free, No API Key needed
- Records we fetched: 1,312 drug recalls
- Time Period: May 2024 to May 2026 (2 years)
- Updated: Daily by FDA

WHAT IS IN THE DATA:

- recall_number → unique ID for each recall
- product_description → what drug was recalled
- reason_for_recall → why it was recalled
- classification → how dangerous (Class I/II/III)
- status → ongoing or completed
- recalling_firm → which company recalled
- state/country → where company is located
- recall_date → when recall started
- brand_name → commercial drug name
- generic_name → scientific drug name
- route → how taken (oral/IV/topical)

CLASSIFICATION MEANING:

- Class I = can cause death or serious harm
- Class II = can cause temporary harm
- Class III = minor issue, unlikely to cause harm

📋 SECTION 2 — ETL Process
EXTRACT:

- Connected to OpenFDA API using Python Requests
- Used pagination to fetch ALL 1,312 records
  (API only gives 100 at a time, so we looped)
- Flattened nested JSON fields (brand_name etc)
- Handled errors (timeouts, empty responses)

TRANSFORM:

- Converted date "20260401" → 2026-04-01 (real date)
- Added risk_score numbers:
  Class I = 10, Class II = 6, Class III = 3
- Categorized recall reasons into buckets:
  contamination, quality, labeling, potency etc
- Cleaned company names:
  "ABC Corp., Inc." → "ABC Corp"
- Removed duplicate records
- Filled empty/null fields

LOAD:

- Connected to PostgreSQL database
- Used UPSERT logic (no duplicates ever)
- Created 3 tables:
  - drug_recalls (main data)
  - company_recall_summary (analytics)
  - pipeline_logs (monitoring)
- Logged every pipeline run

📋 SECTION 3 — Automation (Airflow)
TOOL: Apache Airflow
SCHEDULE: Every day at 8:00 AM automatically

PIPELINE FLOW:
Start → Extract → Transform → Load → Quality Check → End

QUALITY CHECKS:

- Verifies total record count
- Checks for null values
- Validates no future dates
- Confirms pipeline ran successfully

RETRY LOGIC:

- If pipeline fails → retries 2 times
- Waits 5 minutes between retries

📋 SECTION 4 — Analytics (SQL)
WROTE 12 SQL QUERIES ANSWERING:

1. Show all recalls with full details
2. How many recalls per severity level?
3. Top 10 companies with most recalls
4. Why are drugs recalled? (by category)
5. Which US states have most recalls?
6. Voluntary vs forced recalls
7. How many recalls still active?
8. Most dangerous ongoing recalls
9. Monthly recall trends (2024-2026)
10. Which drug types recalled most?
11. Nationwide vs regional recalls
12. Is pipeline running correctly?

KEY FINDINGS:

- Glenmark Pharmaceuticals → 95 recalls (worst!)
- DermaRite → 4 Class I (most dangerous)
- October 2025 → 119 recalls (worst month)
- 88% recalls still ONGOING
- 99.9% companies self-report

📋 SECTION 5 — Power BI Dashboard
CONNECTED: Power BI → PostgreSQL directly

BUILT 9 VISUALS:

1. KPI Card → Total Recalls (1,312)
2. KPI Card → Total Companies (270)
3. KPI Card → Class I Recalls (83)
4. KPI Card → Average Risk Score (5.97)
5. Bar Chart → Top 10 Companies by recalls
6. Line Chart → Monthly Recall Trends
7. Pie Chart → Classification Breakdown
8. Bar Chart → Top Recall Reasons
9. Donut Chart → Recall Status (88% Ongoing)
