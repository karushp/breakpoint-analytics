"""
Build features and calculate analytics from match data.
"""
import pandas as pd
import os
from pathlib import Path
from analytics.config import DATA_RAW_DIR, DATA_PROCESSED_DIR
from analytics.elo import EloRating
from analytics.feature_engineering import FeatureEngineer


def build_all_features(matches_df: pd.DataFrame) -> dict:
    """
    Build all features and analytics from match data.
    
    Args:
        matches_df: DataFrame with normalized match data
        
    Returns:
        Dictionary with all computed features
    """
    print("Building Elo ratings...")
    elo_system = EloRating()
    elo_system.calculate_ratings_from_matches(matches_df)
    
    print("Building feature engineer...")
    feature_engineer = FeatureEngineer(matches_df)
    
    # Get all unique players
    all_players = set(matches_df['winner_id'].unique()) | set(matches_df['loser_id'].unique())
    print(f"Processing {len(all_players)} players...")
    
    # Build player summaries
    player_summaries = []
    for player_id in all_players:
        career_stats = feature_engineer.get_career_stats(player_id)
        recent_form = feature_engineer.get_recent_form(player_id)
        surface_stats = feature_engineer.get_surface_stats(player_id)
        
        current_elo = elo_system.get_rating(player_id)
        
        player_summaries.append({
            'id': player_id,
            'name': matches_df[matches_df['winner_id'] == player_id]['winner_name_normalized'].iloc[0] 
                    if len(matches_df[matches_df['winner_id'] == player_id]) > 0
                    else matches_df[matches_df['loser_id'] == player_id]['loser_name_normalized'].iloc[0],
            'current_elo': round(current_elo, 1),
            'career_win_pct': career_stats.get('career_win_pct'),
            'matches_played': career_stats.get('total_matches', 0),
            'recent_win_pct': recent_form.get('recent_win_pct'),
            'surface_stats': surface_stats
        })
    
    return {
        'elo_system': elo_system,
        'feature_engineer': feature_engineer,
        'player_summaries': player_summaries,
        'matches_df': matches_df
    }


def main():
    """Main feature building function."""
    print("Starting feature building pipeline...")
    
    # Load normalized match data
    matches_path = os.path.join(DATA_RAW_DIR, "matches_combined.csv")
    if not os.path.exists(matches_path):
        print(f"Error: {matches_path} not found. Run ingest_sackmann.py first.")
        return
    
    matches_df = pd.read_csv(matches_path)
    matches_df['tourney_date'] = pd.to_datetime(matches_df['tourney_date'])
    
    print(f"Loaded {len(matches_df)} matches")
    
    # Build features
    features = build_all_features(matches_df)
    
    # Save processed data
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    
    # Save player summaries
    player_df = pd.DataFrame(features['player_summaries'])
    player_df.to_csv(os.path.join(DATA_PROCESSED_DIR, "players.csv"), index=False)
    print(f"Saved player summaries to {DATA_PROCESSED_DIR}/players.csv")
    
    print("Feature building complete!")


if __name__ == "__main__":
    main()
