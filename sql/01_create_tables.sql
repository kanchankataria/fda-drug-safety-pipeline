-- ============================================
-- FDA Drug Safety Pipeline - Database Schema
-- ============================================

CREATE TABLE IF NOT EXISTS drug_recalls (
    id                          SERIAL PRIMARY KEY,
    recall_number               VARCHAR(100) UNIQUE NOT NULL,
    event_id                    VARCHAR(50),
    product_type                VARCHAR(100),
    product_description         TEXT,
    product_quantity            VARCHAR(200),
    code_info                   TEXT,
    reason_for_recall           TEXT,
    reason_category             VARCHAR(100),
    classification              VARCHAR(50),
    risk_score                  INT,
    status                      VARCHAR(50),
    voluntary_mandated          VARCHAR(100),
    distribution_pattern        TEXT,
    recalling_firm              VARCHAR(300),
    company_clean               VARCHAR(300),
    city                        VARCHAR(100),
    state                       VARCHAR(50),
    postal_code                 VARCHAR(20),
    country                     VARCHAR(100),
    brand_name                  VARCHAR(300),
    generic_name                VARCHAR(300),
    route                       VARCHAR(100),
    substance_name              VARCHAR(300),
    recall_initiation_date      DATE,
    report_date                 DATE,
    center_classification_date  DATE,
    termination_date            DATE,
    extracted_at                TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS company_recall_summary (
    id                  SERIAL PRIMARY KEY,
    company_clean       VARCHAR(300) UNIQUE,
    total_recalls       INT DEFAULT 0,
    class_1_recalls     INT DEFAULT 0,
    class_2_recalls     INT DEFAULT 0,
    class_3_recalls     INT DEFAULT 0,
    avg_risk_score      FLOAT,
    is_repeat_offender  BOOLEAN DEFAULT FALSE,
    last_recall_date    DATE,
    updated_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pipeline_logs (
    id               SERIAL PRIMARY KEY,
    run_at           TIMESTAMP DEFAULT NOW(),
    records_fetched  INT,
    records_loaded   INT,
    duration_seconds FLOAT,
    status           VARCHAR(20),
    error_message    TEXT
);

CREATE INDEX IF NOT EXISTS idx_recall_date
    ON drug_recalls(recall_initiation_date);
CREATE INDEX IF NOT EXISTS idx_classification
    ON drug_recalls(classification);
CREATE INDEX IF NOT EXISTS idx_company
    ON drug_recalls(company_clean);
CREATE INDEX IF NOT EXISTS idx_status
    ON drug_recalls(status);