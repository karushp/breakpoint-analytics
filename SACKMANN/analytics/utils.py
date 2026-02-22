"""
Utility functions for tennis analytics.

This module provides helper functions for data normalization, validation,
and common calculations used across the analytics package.
"""
import pandas as pd
from typing import Optional, Dict, List, Union
from datetime import datetime, timedelta


def normalize_player_name(name: Union[str, None]) -> str:
    """
    Normalize player names to handle variations.
    
    Normalizes whitespace, case, and handles missing values.
    Future enhancement: Could add lookup table for abbreviated names.
    
    Args:
        name: Raw player name from data (may be None or NaN)
        
    Returns:
        Normalized player name (empty string if input is None/NaN)
        
    Example:
        >>> normalize_player_name("  NOVAK  DJOKOVIC  ")
        'Novak Djokovic'
        >>> normalize_player_name(None)
        ''
    """
    if pd.isna(name) or name is None:
        return ""
    
    if not isinstance(name, str):
        name = str(name)
    
    # Remove extra whitespace and normalize case
    return " ".join(name.split()).strip().title()


def create_player_id(name: str) -> str:
    """
    Create a stable player ID from normalized name.
    
    Uses format: "lastname-firstinitial" (e.g., "djokovic-n" for "Novak Djokovic").
    Falls back to lowercase single name if only one part provided.
    
    Args:
        name: Normalized player name
        
    Returns:
        Player ID string (empty string if input is empty)
        
    Example:
        >>> create_player_id("Novak Djokovic")
        'djokovic-n'
        >>> create_player_id("Federer")
        'federer'
    """
    if not name or not isinstance(name, str):
        return ""
    
    parts = name.lower().strip().split()
    if not parts:
        return ""
    
    if len(parts) >= 2:
        # Last name-first initial format
        return f"{parts[-1]}-{parts[0][0]}"
    else:
        return parts[0]


def calculate_win_percentage(
    wins: int,
    losses: int,
    min_matches: int = 5
) -> Optional[float]:
    """
    Calculate win percentage with minimum match threshold.
    
    Returns None if insufficient matches to ensure statistical significance.
    
    Args:
        wins: Number of wins (must be >= 0)
        losses: Number of losses (must be >= 0)
        min_matches: Minimum total matches required to return stat
        
    Returns:
        Win percentage as float between 0.0 and 1.0, or None if insufficient data
        
    Example:
        >>> calculate_win_percentage(8, 2, min_matches=5)
        0.8
        >>> calculate_win_percentage(2, 1, min_matches=5)
        None
    """
    if wins < 0 or losses < 0:
        raise ValueError("Wins and losses must be non-negative")
    
    total = wins + losses
    if total < min_matches or total == 0:
        return None
    
    return wins / total


def get_recent_matches(
    df: pd.DataFrame,
    player_id: str,
    days: int = 30,
    date_column: str = 'tourney_date'
) -> pd.DataFrame:
    """
    Get matches for a player within the last N days.
    
    Args:
        df: DataFrame with match data
        player_id: Player ID to filter
        days: Number of days to look back
        date_column: Name of the date column (default: 'tourney_date')
        
    Returns:
        Filtered DataFrame with player's recent matches
        
    Raises:
        KeyError: If date_column not found in DataFrame
    """
    if date_column not in df.columns:
        raise KeyError(f"Date column '{date_column}' not found in DataFrame")
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Filter by player and date
    player_matches = df[
        ((df['winner_id'] == player_id) | (df['loser_id'] == player_id)) &
        (pd.to_datetime(df[date_column]) >= cutoff_date)
    ]
    
    return player_matches.copy()


def handle_missing_data(value: Union[float, int, str, None], default: Optional[Union[float, int, str]] = None) -> Union[float, int, str, None]:
    """
    Handle missing/null values consistently.
    
    Args:
        value: Value to check (may be None, NaN, or valid value)
        default: Default value to return if missing
        
    Returns:
        Original value if not missing, otherwise default value
        
    Example:
        >>> handle_missing_data(None, default=0)
        0
        >>> handle_missing_data(5.5, default=0)
        5.5
    """
    if pd.isna(value):
        return default
    return value


def convert_to_native_type(val) -> Optional[Union[float, int, List]]:
    """
    Convert numpy/pandas types to native Python types for JSON/CSV serialization.
    
    Args:
        val: Value that may be numpy/pandas type
        
    Returns:
        Native Python type (float/int/list) or None
        
    Example:
        >>> import numpy as np
        >>> convert_to_native_type(np.float64(5.5))
        5.5
        >>> convert_to_native_type(None)
        None
    """
    import numpy as np
    
    if val is None:
        return None
    if isinstance(val, (np.integer, np.floating)):
        return float(val) if isinstance(val, np.floating) else int(val)
    if isinstance(val, (np.ndarray, pd.Series)):
        return val.tolist()
    return val
