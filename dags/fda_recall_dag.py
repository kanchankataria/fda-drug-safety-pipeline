"""
dags/fda_recall_dag.py
-----------------------
Apache Airflow DAG for FDA Drug Safety Pipeline.
Runs automatically every day at 8:00 AM.
Extracts → Transforms → Loads FDA recall data.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

# ============================================
# DEFAULT ARGUMENTS
# ============================================
default_args = {
    "owner": "data_engineer",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


# ============================================
# TASK FUNCTIONS
# ============================================


def run_extract(**context):
    """Extract drug recalls from OpenFDA API."""
    from etl.extract import extract
    from config.config import DAYS_TO_FETCH

    print("🔵 Starting Extract Phase...")
    records = extract(days_back=DAYS_TO_FETCH)

    # Pass records to next task via XCom
    context["ti"].xcom_push(key="raw_records", value=records)
    print(f"✅ Extracted {len(records)} records")
    return len(records)


def run_transform(**context):
    """Transform and clean extracted records."""
    from etl.transform import transform

    print("🟡 Starting Transform Phase...")

    # Get records from previous task
    records = context["ti"].xcom_pull(key="raw_records", task_ids="extract_task")

    if not records:
        raise ValueError("No records received from extract task!")

    df = transform(records)
    print(f"✅ Transformed {len(df)} records")

    # Pass DataFrame as dict to next task
    context["ti"].xcom_push(key="transformed_data", value=df.to_dict(orient="records"))
    return len(df)


def run_load(**context):
    """Load transformed data into PostgreSQL."""
    import pandas as pd
    from etl.load import load

    print("🟢 Starting Load Phase...")

    # Get transformed data from previous task
    data = context["ti"].xcom_pull(key="transformed_data", task_ids="transform_task")

    if not data:
        raise ValueError("No data received from transform task!")

    df = pd.DataFrame(data)
    raw_count = len(df)

    success = load(df, raw_count=raw_count)

    if not success:
        raise Exception("Load phase failed!")

    print(f"✅ Load phase complete!")
    return raw_count


def run_quality_check(**context):
    """
    Data quality check after loading.
    Verifies records were loaded correctly.
    """
    import psycopg2
    from config.config import DB_CONFIG

    print("🔍 Running Data Quality Checks...")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Check 1: Total records
    cursor.execute("SELECT COUNT(*) FROM drug_recalls;")
    total = cursor.fetchone()[0]
    print(f"   ✅ Total records in DB: {total}")

    # Check 2: No nulls in critical fields
    cursor.execute("""
        SELECT COUNT(*) FROM drug_recalls
        WHERE classification IS NULL
        AND status IS NULL;
    """)
    nulls = cursor.fetchone()[0]
    print(f"   ✅ Records with null classification+status: {nulls}")

    # Check 3: Latest pipeline run status
    cursor.execute("""
        SELECT status, records_loaded, run_at
        FROM pipeline_logs
        ORDER BY run_at DESC
        LIMIT 1;
    """)
    last_run = cursor.fetchone()
    print(f"   ✅ Last run: {last_run}")

    # Check 4: Verify no future dates
    cursor.execute("""
        SELECT COUNT(*) FROM drug_recalls
        WHERE recall_initiation_date > CURRENT_DATE;
    """)
    future = cursor.fetchone()[0]
    print(f"   ✅ Records with future dates: {future}")

    cursor.close()
    conn.close()

    if nulls > 100:
        raise ValueError(f"Too many null records: {nulls}")
    if future > 0:
        raise ValueError(f"Found {future} records with future dates!")

    print("✅ All quality checks passed!")


# ============================================
# DAG DEFINITION
# ============================================
with DAG(
    dag_id="fda_drug_safety_pipeline",
    default_args=default_args,
    description="Daily FDA Drug Recall ETL Pipeline",
    schedule_interval="0 8 * * *",  # every day at 8:00 AM
    catchup=False,
    tags=["fda", "etl", "drug-safety"],
    max_active_runs=1,
) as dag:

    # ─────────────────────────────────────
    # TASK 1: Start
    # ─────────────────────────────────────
    start = EmptyOperator(task_id="start")

    # ─────────────────────────────────────
    # TASK 2: Extract
    # ─────────────────────────────────────
    extract_task = PythonOperator(
        task_id="extract_task",
        python_callable=run_extract,
        provide_context=True,
    )

    # ─────────────────────────────────────
    # TASK 3: Transform
    # ─────────────────────────────────────
    transform_task = PythonOperator(
        task_id="transform_task",
        python_callable=run_transform,
        provide_context=True,
    )

    # ─────────────────────────────────────
    # TASK 4: Load
    # ─────────────────────────────────────
    load_task = PythonOperator(
        task_id="load_task",
        python_callable=run_load,
        provide_context=True,
    )

    # ─────────────────────────────────────
    # TASK 5: Quality Check
    # ─────────────────────────────────────
    quality_check = PythonOperator(
        task_id="quality_check",
        python_callable=run_quality_check,
        provide_context=True,
    )

    # ─────────────────────────────────────
    # TASK 6: End
    # ─────────────────────────────────────
    end = EmptyOperator(task_id="end")

    # ─────────────────────────────────────
    # PIPELINE FLOW
    # ─────────────────────────────────────
    start >> extract_task >> transform_task >> load_task >> quality_check >> end
