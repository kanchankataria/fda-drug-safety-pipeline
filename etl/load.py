"""
etl/load.py
------------
Loads transformed FDA recall data into PostgreSQL.
Handles upserts, company summaries, and pipeline logging.
"""

import time
import psycopg2
import pandas as pd
from psycopg2.extras import execute_values
from config.config import DB_CONFIG


def get_connection():
    """Create and return a PostgreSQL connection."""
    return psycopg2.connect(**DB_CONFIG)


def load_recalls(df: pd.DataFrame, conn) -> int:
    """
    Load drug recall records into drug_recalls table.
    Uses UPSERT — skips records that already exist.
    Returns number of records loaded.
    """
    if df.empty:
        print("   ⚠️ No records to load!")
        return 0

    cursor = conn.cursor()
    loaded = 0

    # Prepare records as list of tuples
    records = []
    for _, row in df.iterrows():
        records.append(
            (
                row.get("recall_number"),
                row.get("event_id"),
                row.get("product_type"),
                row.get("product_description"),
                row.get("product_quantity"),
                row.get("code_info"),
                row.get("reason_for_recall"),
                row.get("reason_category"),
                row.get("classification"),
                row.get("risk_score"),
                row.get("status"),
                row.get("voluntary_mandated"),
                row.get("distribution_pattern"),
                row.get("recalling_firm"),
                row.get("company_clean"),
                row.get("city"),
                row.get("state"),
                row.get("postal_code"),
                row.get("country"),
                row.get("brand_name"),
                row.get("generic_name"),
                row.get("route"),
                row.get("substance_name"),
                row.get("recall_initiation_date"),
                row.get("report_date"),
                row.get("center_classification_date"),
                row.get("termination_date"),
            )
        )

    # UPSERT — insert new, skip existing (based on recall_number)
    query = """
        INSERT INTO drug_recalls (
            recall_number, event_id, product_type,
            product_description, product_quantity, code_info,
            reason_for_recall, reason_category,
            classification, risk_score, status,
            voluntary_mandated, distribution_pattern,
            recalling_firm, company_clean,
            city, state, postal_code, country,
            brand_name, generic_name, route, substance_name,
            recall_initiation_date, report_date,
            center_classification_date, termination_date
        )
        VALUES %s
        ON CONFLICT (recall_number) DO UPDATE SET
        risk_score     = EXCLUDED.risk_score,
        reason_category = EXCLUDED.reason_category,
        company_clean  = EXCLUDED.company_clean,
        status         = EXCLUDED.status;
    """

    try:
        execute_values(cursor, query, records)
        loaded = cursor.rowcount
        conn.commit()
        print(f"   ✅ Loaded {loaded} new records into drug_recalls")
    except Exception as e:
        conn.rollback()
        print(f"   ❌ Error loading recalls: {e}")
    finally:
        cursor.close()

    return loaded


def update_company_summary(conn):
    """
    Rebuild company_recall_summary table from drug_recalls.
    Identifies repeat offenders (3+ recalls).
    """
    cursor = conn.cursor()

    try:
        # Clear and rebuild summary
        cursor.execute("DELETE FROM company_recall_summary;")

        cursor.execute("""
            INSERT INTO company_recall_summary (
                company_clean,
                total_recalls,
                class_1_recalls,
                class_2_recalls,
                class_3_recalls,
                avg_risk_score,
                is_repeat_offender,
                last_recall_date
            )
            SELECT
                company_clean,
                COUNT(*)                                         AS total_recalls,
                COUNT(*) FILTER (WHERE classification = 'Class I')   AS class_1_recalls,
                COUNT(*) FILTER (WHERE classification = 'Class II')  AS class_2_recalls,
                COUNT(*) FILTER (WHERE classification = 'Class III') AS class_3_recalls,
                ROUND(AVG(risk_score)::NUMERIC, 2)              AS avg_risk_score,
                COUNT(*) >= 3                                    AS is_repeat_offender,
                MAX(recall_initiation_date)                      AS last_recall_date
            FROM drug_recalls
            WHERE company_clean IS NOT NULL
            GROUP BY company_clean
            ORDER BY total_recalls DESC;
        """)

        conn.commit()
        print(f"   ✅ Company summary updated")

    except Exception as e:
        conn.rollback()
        print(f"   ❌ Error updating company summary: {e}")
    finally:
        cursor.close()


def log_pipeline_run(
    conn, fetched: int, loaded: int, duration: float, status: str, error: str = None
):
    """Log every pipeline run for monitoring."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO pipeline_logs
                (records_fetched, records_loaded, duration_seconds, status, error_message)
            VALUES (%s, %s, %s, %s, %s);
        """,
            (fetched, loaded, duration, status, error),
        )
        conn.commit()
        print(f"   ✅ Pipeline run logged")
    except Exception as e:
        conn.rollback()
        print(f"   ❌ Error logging run: {e}")
    finally:
        cursor.close()


def load(df: pd.DataFrame, raw_count: int = 0) -> bool:
    """
    Main load function.
    Loads data into PostgreSQL and updates summaries.
    """
    print("\n" + "=" * 60)
    print("📤 LOAD PHASE STARTING")
    print("=" * 60)

    start_time = time.time()
    status = "success"
    error_msg = None
    loaded = 0

    try:
        conn = get_connection()
        print(f"   ✅ Connected to PostgreSQL!")

        # Load recalls
        loaded = load_recalls(df, conn)

        # Update company summary
        update_company_summary(conn)

        duration = round(time.time() - start_time, 2)

        # Log the run
        log_pipeline_run(conn, raw_count, loaded, duration, status)

        print(f"\n   ⏱️  Load completed in {duration}s")
        print("=" * 60)

        conn.close()
        return True

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        status = "failed"
        error_msg = str(e)
        print(f"   ❌ Load failed: {e}")
        log_pipeline_run(conn, raw_count, 0, duration, status, error_msg)
        return False


# ──────────────────────────────────────────
# Quick test (run this file directly)
# ──────────────────────────────────────────
if __name__ == "__main__":
    from etl.extract import extract
    from etl.transform import transform

    # Run full ETL
    from config.config import DAYS_TO_FETCH
    raw = extract(days_back=DAYS_TO_FETCH)
    df = transform(raw)
    load(df, raw_count=len(raw))

    # Verify data in database
    print("\n🔍 VERIFYING DATA IN POSTGRESQL...")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM drug_recalls;")
    total = cursor.fetchone()[0]
    print(f"   📊 Total records in drug_recalls: {total}")

    cursor.execute("""
        SELECT recall_number, classification, risk_score,
               company_clean, recall_initiation_date
        FROM drug_recalls
        ORDER BY recall_initiation_date DESC
        LIMIT 5;
    """)
    rows = cursor.fetchall()
    print(f"\n   📋 Latest 5 recalls in DB:")
    print(f"   {'─' * 70}")
    for row in rows:
        print(
            f"   {str(row[0]):15} {str(row[1]):12} "
            f"risk:{row[2]}  {str(row[3])[:30]:30} {str(row[4])}"
        )

    cursor.execute("SELECT COUNT(*) FROM pipeline_logs;")
    runs = cursor.fetchone()[0]
    print(f"\n   📝 Total pipeline runs logged: {runs}")

    cursor.close()
    conn.close()
