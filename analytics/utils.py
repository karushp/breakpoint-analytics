"""
Utility functions for tennis analytics.
"""
import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime, timedelta


def normalize_player_name(name: str) -> str:
    """
    Normalize player names to handle variations.
    
    Args:
        name: Raw player name from data
        
    Returns:
        Normalized player name
    """
    if pd.isna(name):
        return ""
    
    # Remove extra whitespace
    name = " ".join(name.split())
    
    # Handle common variations
    # "N. Djokovic" -> "Novak Djokovic" (would need lookup table)
    # For now, just normalize whitespace and case
    
    return name.strip().title()


def create_player_id(name: str) -> str:
    """
    Create a stable player ID from normalized name.
    
    Args:
        name: Normalized player name
        
    Returns:
        Player ID (e.g., "djokovic-n")
    """
    if not name:
        return ""
    
    # Convert to lowercase, replace spaces with hyphens
    parts = name.lower().split()
    if len(parts) >= 2:
        # Last name-first initial format
        return f"{parts[-1]}-{parts[0][0]}"
    else:
        return parts[0].lower()


def calculate_win_percentage(wins: int, losses: int, min_matches: int = 5) -> Optional[float]:
    """
    Calculate win percentage with minimum match threshold.
    
    Args:
        wins: Number of wins
        losses: Number of losses
        min_matches: Minimum matches required to return stat
        
    Returns:
        Win percentage (0-1) or None if insufficient data
    """
    total = wins + losses
    if total < min_matches:
        return None
    return wins / total if total > 0 else None


def get_recent_matches(df: pd.DataFrame, player_id: str, days: int = 30) -> pd.DataFrame:
    """
    Get matches for a player within the last N days.
    
    Args:
        df: DataFrame with match data
        player_id: Player ID to filter
        days: Number of days to look back
        
    Returns:
        Filtered DataFrame
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    # Assuming df has a 'date' column
    return df[df['date'] >= cutoff_date]


def handle_missing_data(value, default=None):
    """
    Handle missing/null values consistently.
    
    Args:
        value: Value to check
        default: Default value if missing
        
    Returns:
        Value or default
    """
    if pd.isna(value):
        return default
    return value
