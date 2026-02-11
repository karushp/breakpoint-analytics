"""
Breakpoint Analytics - Tennis Analytics Package

This package provides tools for analyzing tennis match data, calculating
Elo ratings, engineering features, and predicting match outcomes.
"""

from analytics.elo import EloRating
from analytics.feature_engineering import FeatureEngineer
from analytics.win_probability import WinProbabilityCalculator
from analytics.score_parser import ScoreParser, parse_tennis_score
from analytics.metrics_comparator import MetricsComparator
from analytics.utils import (
    normalize_player_name,
    create_player_id,
    calculate_win_percentage,
    get_recent_matches,
    handle_missing_data,
    convert_to_native_type
)

__all__ = [
    # Core classes
    'EloRating',
    'FeatureEngineer',
    'WinProbabilityCalculator',
    'ScoreParser',
    'MetricsComparator',
    
    # Utility functions
    'parse_tennis_score',
    'normalize_player_name',
    'create_player_id',
    'calculate_win_percentage',
    'get_recent_matches',
    'handle_missing_data',
    'convert_to_native_type',
]

__version__ = '0.1.0'
