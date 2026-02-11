"""
Configuration constants for tennis analytics.
"""

# Elo Configuration
ELO_STARTING_RATING = 1500
ELO_K_FACTOR_REGULAR = 32
ELO_K_FACTOR_GRAND_SLAM = 48
ELO_K_FACTOR_SMALL = 24
ELO_DECAY_CONSTANT_DAYS = 365  # Matches older than this have reduced weight

# Surface Adjustments (additive to base Elo)
SURFACE_ADJUSTMENTS = {
    'Hard': 0,
    'Clay': -50,  # Example: clay specialists get +50 boost on clay
    'Grass': 30,  # Example: grass specialists get +30 boost on grass
    'Carpet': 0
}

# Feature Engineering
MIN_MATCHES_FOR_STATS = 5
MIN_MATCHES_FOR_SURFACE_STATS = 3
RECENT_FORM_MATCHES = 10
RECENT_FORM_DAYS = 90  # Look back 90 days for recent form
MIN_MATCHES_FOR_EXPORT = 10  # Minimum matches for player to appear in exports

# Data Sources
SACKMANN_REPO_URL = "https://github.com/JeffSackmann/tennis_atp"
SACKMANN_CSV_BASE_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master"

# File Paths
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
OUTPUTS_DIR = "outputs"

# Tournament Levels (for weighting)
GRAND_SLAM_LEVELS = ['G']
MASTERS_LEVELS = ['M']
ATP_250_LEVELS = ['250']
ATP_500_LEVELS = ['500']

# Metric Weights for Win Probability Calculation
# These weights determine how much each metric influences win probability
# Higher weight = more predictive power
# Total should ideally sum to 1.0, but can be adjusted
METRIC_WEIGHTS = {
    'avg_winning_margin': 0.12,      # Dominance indicator - higher margin = stronger player
    'first_set_win_pct': 0.15,       # Strong predictor - winning first set correlates with match wins
    'second_set_win_pct': 0.12,      # Important but less than first set
    'ace_pct': 0.08,                  # Serve strength indicator
    'avg_minutes_for_wins': 0.04,     # Efficiency - lower is better (inverted in calculation)
    'avg_losing_game_time': 0.04,     # Resilience - lower is better (inverted in calculation)
    'avg_opponent_age_when_won': 0.08,  # Context - younger opponents may be easier
    'avg_opponent_age_when_lost': 0.08, # Context - older opponents may be tougher
    'surface_match': 0.08,            # Surface advantage/disadvantage
    'form_last_10_wins': 0.12,        # Recent form - average of last 10 wins (higher weight)
    'form_last_5_wins': 0.09,         # Very recent form - average of last 5 wins
}

# Hybrid Probability Weights
# How much to weight Elo vs Metrics in final probability
ELO_WEIGHT = 0.65  # Elo gets 65% weight
METRICS_WEIGHT = 0.35  # Metrics get 35% weight

# Fallback Configuration
USE_METRICS_FALLBACK = True  # If True, fall back to Elo-only if insufficient metrics
MIN_METRICS_REQUIRED = 3  # Minimum number of non-null metrics required to use metric-based prob

# Validation Configuration
VALIDATION_TRAIN_SPLIT = 0.8  # 80% of data for training, 20% for testing
VALIDATION_MIN_TRAIN_MATCHES = 100  # Minimum matches required in training set
VALIDATION_MIN_TEST_MATCHES = 50  # Minimum matches required in test set
