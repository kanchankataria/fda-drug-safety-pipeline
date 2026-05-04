"""
config/config.py
-----------------
Central configuration for the FDA Drug Safety Pipeline.
Loads settings from .env file and exposes them as Python variables.
"""

import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()


# ============================================
# DATABASE CONFIGURATION
# ============================================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "fda_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}


# ============================================
# API CONFIGURATION
# ============================================
OPENFDA_BASE_URL = "https://api.fda.gov/drug/enforcement.json"

# Number of records to fetch per API call (max 1000)
API_LIMIT = 100

# How many days back to fetch data
DAYS_TO_FETCH = 730

# API timeout in seconds
API_TIMEOUT = 15


# ============================================
# PIPELINE CONFIGURATION
# ============================================
PROJECT_NAME = "fda-drug-safety-pipeline"

# Risk score mapping (we'll use this in transform.py)
RISK_SCORE_MAP = {
    "Class I": 10,  # most serious
    "Class II": 6,  # moderate
    "Class III": 3,  # least serious
}

# Reason categories (we'll use this in transform.py)
REASON_CATEGORIES = {
    "contamination": ["microbial", "bacterial", "contamination", "sterility"],
    "labeling": ["mislabel", "label", "incorrect labeling"],
    "potency": ["potency", "subpotent", "superpotent", "strength"],
    "quality": ["dissolution", "stability", "impurit", "particulate"],
    "packaging": ["packaging", "container", "leak"],
    "manufacturing": ["manufacturing", "process", "GMP"],
}


# ============================================
# QUICK TEST (Run this file directly to verify)
# ============================================
if __name__ == "__main__":
    print("\n🔧 CONFIG LOADED SUCCESSFULLY")
    print("=" * 50)
    print(f"Database:  {DB_CONFIG['database']}")
    print(f"Host:      {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"User:      {DB_CONFIG['user']}")
    print(f"API URL:   {OPENFDA_BASE_URL}")
    print(f"Days back: {DAYS_TO_FETCH}")
    print("=" * 50 + "\n")
