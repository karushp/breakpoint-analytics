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

# File paths (relative to project root)
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
OUTPUTS_DIR = "outputs"

# Feature / model constants (used by pipelines/features.py and train_model.py)
ROLL_WINDOW = 10       # Rolling stats window (e.g. win %, aces, minutes)
LAST_N_WIN_AVG = 3     # "Previous N games" win average (e.g. last 3)
ELO_K = 32             # ELO update step size
ELO_INIT = 1500.0      # Starting ELO for new players
ELO_SCALE = 400.0      # ELO formula scale: expected = 1 / (1 + 10^((R_opp - R) / ELO_SCALE))

# Train/val/test split (time-based; test = 1 - TRAIN_FRAC - VAL_FRAC)
TRAIN_FRAC = 0.6
VAL_FRAC = 0.2

# XGBoost defaults (pipelines/train_model.py)
XGB_N_ESTIMATORS = 300
XGB_MAX_DEPTH = 4
XGB_LEARNING_RATE = 0.05
XGB_SUBSAMPLE = 0.8
XGB_COLSAMPLE_BYTREE = 0.8
XGB_EARLY_STOPPING_ROUNDS = 20
XGB_RANDOM_STATE = 42

# Output artifact filenames (under OUTPUTS_DIR)
MODEL_FILENAME = "model.pkl"
FEATURE_COLS_FILENAME = "feature_cols.json"
PLAYER_STATS_FILENAME = "player_stats_latest.csv"
