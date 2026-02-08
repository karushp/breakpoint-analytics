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
