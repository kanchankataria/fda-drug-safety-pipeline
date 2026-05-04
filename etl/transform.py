"""
etl/transform.py
-----------------
Cleans, enriches, and transforms raw FDA recall data.
Adds risk scoring, reason categorization, and company standardization.
"""

import re
import pandas as pd
from datetime import datetime
from config.config import RISK_SCORE_MAP, REASON_CATEGORIES


def parse_date(date_str: str):
    """Convert YYYYMMDD string to Python date object."""
    if not date_str or date_str.strip() == "":
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y%m%d").date()
    except ValueError:
        return None


def get_risk_score(classification: str) -> int:
    if not classification:
        return 0
    # Use exact match instead of substring check
    classification = classification.strip()
    return RISK_SCORE_MAP.get(classification, 0)


def get_reason_category(reason: str) -> str:
    """Categorize the recall reason into broad buckets."""
    if not reason:
        return "unknown"
    reason_lower = reason.lower()
    for category, keywords in REASON_CATEGORIES.items():
        if any(kw in reason_lower for kw in keywords):
            return category
    return "other"


def clean_company_name(name: str) -> str:
    """Standardize company names for better grouping."""
    if not name:
        return "Unknown"
    # Remove extra spaces
    name = " ".join(name.split())
    # Remove common suffixes for grouping
    patterns = [
        r",?\s*(Inc\.?|LLC\.?|Ltd\.?|Corp\.?|Co\.?)$",
        r",?\s*(Incorporated|Limited|Corporation|Company)$",
    ]
    for pattern in patterns:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE).strip()
    return name


def clean_text(text: str, max_length: int = 500) -> str:
    """Clean and truncate long text fields."""
    if not text:
        return None
    # Remove extra whitespace
    text = " ".join(text.split())
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    return text


def transform(records: list[dict]) -> pd.DataFrame:
    """
    Main transform function.
    Takes raw extracted records and returns a clean DataFrame.
    """
    print("\n" + "=" * 60)
    print("🔄 TRANSFORM PHASE STARTING")
    print("=" * 60)

    if not records:
        print("   ⚠️ No records to transform!")
        return pd.DataFrame()

    print(f"   📥 Input records:  {len(records)}")

    # Convert to DataFrame
    df = pd.DataFrame(records)

    # ─────────────────────────────────────
    # 1. REMOVE DUPLICATES
    # ─────────────────────────────────────
    before = len(df)
    df.drop_duplicates(subset=["recall_number"], inplace=True)
    print(f"   🗑️  Duplicates removed: {before - len(df)}")

    # ─────────────────────────────────────
    # 2. DROP RECORDS WITHOUT RECALL NUMBER
    # ─────────────────────────────────────
    df.dropna(subset=["recall_number"], inplace=True)

    # ─────────────────────────────────────
    # 3. CONVERT DATE FIELDS
    # ─────────────────────────────────────
    date_fields = [
        "recall_initiation_date",
        "report_date",
        "center_classification_date",
        "termination_date",
    ]
    for field in date_fields:
        df[field] = df[field].apply(parse_date)

    print(f"   📅 Dates converted")

    # ─────────────────────────────────────
    # 4. ADD RISK SCORE
    # ─────────────────────────────────────
    df["risk_score"] = df["classification"].apply(get_risk_score)
    print(f"   🎯 Risk scores added")

    # ─────────────────────────────────────
    # 5. ADD REASON CATEGORY
    # ─────────────────────────────────────
    df["reason_category"] = df["reason_for_recall"].apply(get_reason_category)
    print(f"   🏷️  Reason categories added")

    # ─────────────────────────────────────
    # 6. CLEAN COMPANY NAMES
    # ─────────────────────────────────────
    df["company_clean"] = df["recalling_firm"].apply(clean_company_name)
    print(f"   🏭 Company names standardized")

    # ─────────────────────────────────────
    # 7. CLEAN TEXT FIELDS
    # ─────────────────────────────────────
    df["product_description"] = df["product_description"].apply(clean_text)
    df["reason_for_recall"] = df["reason_for_recall"].apply(clean_text)
    df["distribution_pattern"] = df["distribution_pattern"].apply(clean_text)

    # ─────────────────────────────────────
    # 8. FILL NULL VALUES
    # ─────────────────────────────────────
    df["country"] = df["country"].fillna("United States")
    df["status"] = df["status"].fillna("Unknown")
    df["route"] = df["route"].fillna("Unknown")

    # ─────────────────────────────────────
    # 9. PRINT SUMMARY
    # ─────────────────────────────────────
    print(f"\n   📊 TRANSFORM SUMMARY:")
    print(f"   {'─' * 40}")
    print(f"   Output records:  {len(df)}")

    if "classification" in df.columns:
        print(f"\n   Classification breakdown:")
        for cls, count in df["classification"].value_counts().items():
            emoji = (
                "🔴"
                if "I " in cls or cls.endswith("I")
                else "🟡" if "II" in cls else "🟢"
            )
            print(f"   {emoji} {cls:15} → {count} recalls")

    if "reason_category" in df.columns:
        print(f"\n   Top reason categories:")
        for cat, count in df["reason_category"].value_counts().head(5).items():
            print(f"   📌 {cat:20} → {count}")

    print("=" * 60)
    return df


# ──────────────────────────────────────────
# Quick test (run this file directly)
# ──────────────────────────────────────────
if __name__ == "__main__":
    from etl.extract import extract

    raw = extract(days_back=30)
    df = transform(raw)

    print("\n📋 TRANSFORMED DATA SAMPLE:")
    print(
        df[
            [
                "recall_number",
                "classification",
                "risk_score",
                "reason_category",
                "company_clean",
                "recall_initiation_date",
            ]
        ].to_string(index=False)
    )
