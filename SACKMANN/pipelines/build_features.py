"""
Build features and calculate analytics from match data.

This pipeline:
1. Loads normalized match data
2. Calculates Elo ratings for all players
3. Computes comprehensive statistics and metrics for each player
4. Saves player summaries to CSV
"""
import pandas as pd
import os
from typing import Dict, List, Optional
from analytics.config import DATA_RAW_DIR, DATA_PROCESSED_DIR
from analytics.elo import EloRating
from analytics.feature_engineering import FeatureEngineer


def _create_player_name_lookup(matches_df: pd.DataFrame) -> Dict[str, str]:
    """
    Create a lookup dictionary mapping player_id to player name.
    
    More efficient than filtering DataFrame multiple times.
    
    Args:
        matches_df: DataFrame with match data
        
    Returns:
        Dictionary mapping player_id to player name
    """
    name_lookup = {}
    
    # Get names from winners
    winner_names = matches_df[['winner_id', 'winner_name_normalized']].drop_duplicates()
    for _, row in winner_names.iterrows():
        if pd.notna(row['winner_id']) and pd.notna(row['winner_name_normalized']):
            name_lookup[row['winner_id']] = row['winner_name_normalized']
    
    # Fill in any missing names from losers
    loser_names = matches_df[['loser_id', 'loser_name_normalized']].drop_duplicates()
    for _, row in loser_names.iterrows():
        player_id = row['loser_id']
        if pd.notna(player_id) and player_id not in name_lookup:
            if pd.notna(row['loser_name_normalized']):
                name_lookup[player_id] = row['loser_name_normalized']
    
    return name_lookup


def _build_player_summary(
    player_id: str,
    name: str,
    elo_system: EloRating,
    feature_engineer: FeatureEngineer
) -> Dict:
    """
    Build a single player's summary with all statistics.
    
    Args:
        player_id: Player identifier
        name: Player name
        elo_system: EloRating instance
        feature_engineer: FeatureEngineer instance
        
    Returns:
        Dictionary with player summary
    """
    career_stats = feature_engineer.get_career_stats(player_id)
    recent_form = feature_engineer.get_recent_form(player_id)
    surface_stats = feature_engineer.get_surface_stats(player_id)
    detailed_metrics = feature_engineer.get_detailed_player_metrics(player_id)
    current_elo = elo_system.get_rating(player_id)
    
    return {
        'id': player_id,
        'name': name,
        'current_elo': round(current_elo, 1),
        'career_win_pct': career_stats.get('career_win_pct'),
        'matches_played': career_stats.get('total_matches', 0),
        'recent_win_pct': recent_form.get('recent_win_pct'),
        'surface_stats': surface_stats,
        'detailed_metrics': detailed_metrics
    }


def build_all_features(matches_df: pd.DataFrame) -> Dict:
    """
    Build all features and analytics from match data.
    
    Args:
        matches_df: DataFrame with normalized match data
        
    Returns:
        Dictionary with all computed features containing:
        - elo_system: EloRating instance
        - feature_engineer: FeatureEngineer instance
        - player_summaries: List of player summary dictionaries
        - matches_df: Original matches DataFrame
        
    Raises:
        ValueError: If required columns are missing
        KeyError: If critical columns are not found
    """
    # Validate required columns
    required_columns = ['winner_id', 'loser_id', 'tourney_date']
    missing_columns = [col for col in required_columns if col not in matches_df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    print("Building Elo ratings...")
    elo_system = EloRating()
    elo_system.calculate_ratings_from_matches(matches_df)
    
    print("Building feature engineer...")
    feature_engineer = FeatureEngineer(matches_df)
    
    # Get all unique players
    all_players = set(matches_df['winner_id'].unique()) | set(matches_df['loser_id'].unique())
    all_players = {p for p in all_players if pd.notna(p)}  # Remove NaN values
    print(f"Processing {len(all_players)} players...")
    
    # Create efficient name lookup
    name_lookup = _create_player_name_lookup(matches_df)
    
    # Build player summaries with progress indication
    player_summaries = []
    total_players = len(all_players)
    
    for idx, player_id in enumerate(all_players, 1):
        # Get player name (with fallback)
        player_name = name_lookup.get(player_id, f"Unknown Player ({player_id})")
        
        # Build summary
        summary = _build_player_summary(
            player_id, player_name, elo_system, feature_engineer
        )
        player_summaries.append(summary)
        
        # Progress indication for large datasets
        if total_players > 100 and idx % 50 == 0:
            print(f"  Processed {idx}/{total_players} players ({idx/total_players*100:.1f}%)")
    
    print(f"Completed processing {len(player_summaries)} players")
    
    return {
        'elo_system': elo_system,
        'feature_engineer': feature_engineer,
        'player_summaries': player_summaries,
        'matches_df': matches_df
    }


def _load_match_data(data_path: str) -> pd.DataFrame:
    """
    Load and validate match data from CSV file.
    
    Args:
        data_path: Path to matches CSV file
        
    Returns:
        DataFrame with match data
        
    Raises:
        FileNotFoundError: If data file doesn't exist
        ValueError: If data loading fails
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Match data file not found: {data_path}\n"
            "Please run ingest_sackmann.py first to download and normalize data."
        )
    
    try:
        matches_df = pd.read_csv(data_path)
        
        # Ensure date column is datetime
        if 'tourney_date' in matches_df.columns:
            matches_df['tourney_date'] = pd.to_datetime(matches_df['tourney_date'], errors='coerce')
        
        return matches_df
    except Exception as e:
        raise ValueError(f"Failed to load match data: {e}")


def _save_player_summaries(player_summaries: List[Dict], output_path: str) -> None:
    """
    Save player summaries to CSV file.
    
    Args:
        player_summaries: List of player summary dictionaries
        output_path: Path to save CSV file
        
    Raises:
        IOError: If file writing fails
    """
    try:
        player_df = pd.DataFrame(player_summaries)
        player_df.to_csv(output_path, index=False)
    except Exception as e:
        raise IOError(f"Failed to save player summaries to {output_path}: {e}")


def main() -> None:
    """
    Main feature building function.
    
    Orchestrates the feature building pipeline:
    1. Loads normalized match data
    2. Builds all features (Elo + Metrics)
    3. Saves player summaries to CSV
    """
    print("=" * 60)
    print("Starting feature building pipeline...")
    print("=" * 60)
    
    # Load normalized match data
    matches_path = os.path.join(DATA_RAW_DIR, "matches_combined.csv")
    
    try:
        matches_df = _load_match_data(matches_path)
        print(f"✓ Loaded {len(matches_df):,} matches")
    except (FileNotFoundError, ValueError) as e:
        print(f"✗ Error: {e}")
        return
    
    # Build features
    try:
        features = build_all_features(matches_df)
    except (ValueError, KeyError) as e:
        print(f"✗ Error building features: {e}")
        return
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return
    
    # Save processed data
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    output_path = os.path.join(DATA_PROCESSED_DIR, "players.csv")
    
    try:
        _save_player_summaries(features['player_summaries'], output_path)
        print(f"✓ Saved {len(features['player_summaries']):,} player summaries")
        print(f"  Location: {output_path}")
    except IOError as e:
        print(f"✗ Error saving data: {e}")
        return
    
    print("=" * 60)
    print("Feature building complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
