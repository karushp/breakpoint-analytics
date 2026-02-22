"""
Configuration for TennisMyLife data source (stats.tennismylife.org).
"""

# Data source
TENNISMYLIFE_BASE_URL = "https://stats.tennismylife.org/data"
TENNISMYLIFE_YEARS = [2024, 2025, 2026]

# Year CSVs: completed tournaments for that year
def get_tennismylife_year_url(year: int) -> str:
    return f"{TENNISMYLIFE_BASE_URL}/{year}.csv"

# Current / ongoing tournaments (in progress)
# Once a tournament completes, it moves to the current year CSV
TENNISMYLIFE_CURRENT_TOURNEYS_URL = "https://stats.tennismylife.org/data/ongoing_tourneys.csv"

# File paths (relative to TENNISMYLIFE project root)
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
OUTPUTS_DIR = "outputs"
