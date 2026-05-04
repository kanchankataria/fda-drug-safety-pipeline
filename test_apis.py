"""
test_apis.py
-------------
Quick test to verify the OpenFDA API is working
before we build the full ETL pipeline.
"""

import requests
from datetime import datetime, timedelta

print("\n" + "=" * 65)
print("💊 FDA DRUG SAFETY INTELLIGENCE PIPELINE - API TEST")
print("=" * 65)

print("\n[Testing OpenFDA Drug Recalls API ...]\n")

try:
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

    url = (
        f"https://api.fda.gov/drug/enforcement.json"
        f"?search=recall_initiation_date:[{start_date}+TO+{end_date}]"
        f"&limit=10"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    print(f"   ✅ Status Code:           {response.status_code}")
    print(f"   ✅ Total Recalls (30d):   {data['meta']['results']['total']:,}")
    print(f"   ✅ Returned in this call: {len(data['results'])}")

    print("\n" + "─" * 65)
    print("📋 SAMPLE RECALL DATA:")
    print("─" * 65)

    sample = data["results"][0]

    print(f"\n   Recall Number:  {sample.get('recall_number', 'N/A')}")
    print(f"   Product:        {sample.get('product_description', 'N/A')[:80]}...")
    print(f"   Classification: {sample.get('classification', 'N/A')}")
    print(f"   Company:        {sample.get('recalling_firm', 'N/A')}")
    print(f"   State:          {sample.get('state', 'N/A')}")
    print(f"   Recall Date:    {sample.get('recall_initiation_date', 'N/A')}")
    print(f"   Reason:         {sample.get('reason_for_recall', 'N/A')[:80]}...")

except Exception as e:
    print(f"   ❌ ERROR: {e}")

print("\n" + "=" * 65)
print("🎉 API TESTING COMPLETE!")
print("=" * 65 + "\n")
