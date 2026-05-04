"""
etl/extract.py
---------------
Extracts drug recall data from the OpenFDA API.
Handles pagination, errors, and rate limiting.
"""

import requests
import time
from datetime import datetime, timedelta
from config.config import OPENFDA_BASE_URL, API_LIMIT, DAYS_TO_FETCH, API_TIMEOUT


def fetch_recalls(days_back: int = DAYS_TO_FETCH) -> list[dict]:
    """
    Fetch drug recalls from OpenFDA API for the last N days.
    Handles pagination to get ALL records, not just first 100.
    """

    # Build date range
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")

    print(f"\n📡 Fetching recalls from {start_date} to {end_date}...")

    all_records = []
    skip = 0  # pagination offset
    total = None  # total records available

    while True:
        try:
            # Build URL with pagination
            url = (
                f"{OPENFDA_BASE_URL}"
                f"?search=recall_initiation_date:[{start_date}+TO+{end_date}]"
                f"&limit={API_LIMIT}"
                f"&skip={skip}"
            )

            response = requests.get(url, timeout=API_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            # Get total count on first call
            if total is None:
                total = data["meta"]["results"]["total"]
                print(f"   📊 Total records available: {total}")

            # Extract results
            records = data.get("results", [])
            all_records.extend(records)

            print(f"   ✅ Fetched {len(all_records)}/{total} records...")

            # Check if we've fetched everything
            if len(all_records) >= total or len(records) == 0:
                break

            # Move to next page
            skip += API_LIMIT

            # Be polite to the API (avoid rate limiting)
            time.sleep(0.5)

        except requests.exceptions.Timeout:
            print(f"   ⚠️ Request timed out at skip={skip}. Retrying...")
            time.sleep(2)
            continue

        except requests.exceptions.HTTPError as e:
            # 404 means no results found for date range
            if response.status_code == 404:
                print(f"   ⚠️ No records found for this date range.")
                break
            print(f"   ❌ HTTP Error: {e}")
            break

        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            break

    print(f"   🎉 Total records fetched: {len(all_records)}")
    return all_records


def extract_openfda_fields(record: dict) -> dict:
    """
    Safely extract nested openfda fields from a single record.
    openfda is a nested object — not all records have it.
    """
    openfda = record.get("openfda", {})

    # openfda fields are lists — take first item if exists
    def first(lst):
        return lst[0] if lst else None

    return {
        "brand_name": first(openfda.get("brand_name", [])),
        "generic_name": first(openfda.get("generic_name", [])),
        "route": first(openfda.get("route", [])),
        "substance_name": first(openfda.get("substance_name", [])),
    }


def extract(days_back: int = DAYS_TO_FETCH) -> list[dict]:
    """
    Main extract function.
    Fetches raw records and flattens nested openfda fields.
    Returns a clean list of flat dictionaries.
    """
    print("\n" + "=" * 60)
    print("📥 EXTRACT PHASE STARTING")
    print("=" * 60)

    start_time = time.time()

    # Fetch raw records from API
    raw_records = fetch_recalls(days_back)

    if not raw_records:
        print("   ⚠️ No records extracted!")
        return []

    # Flatten each record
    flat_records = []
    for record in raw_records:
        openfda_fields = extract_openfda_fields(record)

        flat = {
            # Identification
            "recall_number": record.get("recall_number"),
            "event_id": record.get("event_id"),
            "product_type": record.get("product_type"),
            # Product
            "product_description": record.get("product_description"),
            "product_quantity": record.get("product_quantity"),
            "code_info": record.get("code_info"),
            # Recall details
            "reason_for_recall": record.get("reason_for_recall"),
            "classification": record.get("classification"),
            "status": record.get("status"),
            "voluntary_mandated": record.get("voluntary_mandated"),
            "distribution_pattern": record.get("distribution_pattern"),
            # Company
            "recalling_firm": record.get("recalling_firm"),
            "city": record.get("city"),
            "state": record.get("state"),
            "postal_code": record.get("postal_code"),
            "country": record.get("country"),
            # Dates
            "recall_initiation_date": record.get("recall_initiation_date"),
            "report_date": record.get("report_date"),
            "center_classification_date": record.get("center_classification_date"),
            "termination_date": record.get("termination_date"),
            # From openfda nested object
            **openfda_fields,
        }
        flat_records.append(flat)

    duration = round(time.time() - start_time, 2)
    print(f"\n✅ Extract complete: {len(flat_records)} records in {duration}s")
    print("=" * 60)

    return flat_records


# ──────────────────────────────────────────
# Quick test (run this file directly)
# ──────────────────────────────────────────
if __name__ == "__main__":
    records = extract(days_back=DAYS_TO_FETCH)

    if records:
        print("\n📋 SAMPLE RECORD (first result):")
        print("-" * 40)
        sample = records[0]
        for key, value in sample.items():
            if value:
                print(f"  {key:35} {str(value)[:60]}")
