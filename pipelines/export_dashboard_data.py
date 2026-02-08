"""
Export processed data to JSON for frontend consumption.
"""
import json
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from analytics.config import DATA_PROCESSED_DIR, OUTPUTS_DIR, DATA_RAW_DIR
from analytics.elo import EloRating
from analytics.feature_engineering import FeatureEngineer
from analytics.win_probability import WinProbabilityCalculator
from pipelines.build_features import build_all_features


def export_player_summary(features: dict) -> dict:
    """
    Export player summary data.
    
    Args:
        features: Dictionary with computed features
        
    Returns:
        Player summary dictionary
    """
    players = []
    elo_system = features['elo_system']
    
    for player_summary in features['player_summaries']:
        # Filter to active players (at least 10 matches)
        if player_summary['matches_played'] >= 10:
            players.append({
                'id': player_summary['id'],
                'name': player_summary['name'],
                'current_elo': player_summary['current_elo'],
                'current_rank': None,  # Would need ranking data
                'career_win_pct': player_summary['career_win_pct'],
                'matches_played': player_summary['matches_played'],
                'active': True  # Could check last match date
            })
    
    # Sort by Elo
    players.sort(key=lambda x: x['current_elo'], reverse=True)
    
    # Add rankings
    for i, player in enumerate(players):
        player['current_rank'] = i + 1
    
    return {
        'players': players,
        'last_updated': datetime.now().isoformat() + 'Z'
    }


def export_matchup_stats(
    player_a_id: str,
    player_b_id: str,
    features: dict
) -> dict:
    """
    Export matchup statistics for two players.
    
    Args:
        player_a_id: First player ID
        player_b_id: Second player ID
        features: Dictionary with computed features
        
    Returns:
        Matchup statistics dictionary
    """
    elo_system = features['elo_system']
    feature_engineer = features['feature_engineer']
    matches_df = features['matches_df']
    
    # Calculate win probability
    win_prob_calc = WinProbabilityCalculator(elo_system)
    
    # Get H2H
    h2h = feature_engineer.get_head_to_head(player_a_id, player_b_id)
    
    # Get surface (default to Hard for now, would be passed from frontend)
    surface = 'Hard'
    win_prob = win_prob_calc.calculate_elo_based_probability(
        player_a_id, player_b_id, surface
    )
    
    # Get form
    form_a = feature_engineer.get_recent_form(player_a_id)
    form_b = feature_engineer.get_recent_form(player_b_id)
    
    # Get surface stats
    surface_stats_a = feature_engineer.get_surface_stats(player_a_id)
    surface_stats_b = feature_engineer.get_surface_stats(player_b_id)
    
    # Build surface comparison
    surface_comparison = {}
    for surface_type in ['Hard', 'Clay', 'Grass']:
        surface_comparison[surface_type.lower()] = {
            'player_a': surface_stats_a.get(surface_type, {}).get('win_pct'),
            'player_b': surface_stats_b.get(surface_type, {}).get('win_pct')
        }
    
    # Get Elo trends (simplified - last 20 matches)
    elo_trends = {
        'player_a': [],  # Would need historical Elo tracking
        'player_b': []
    }
    
    return {
        'player_a_id': player_a_id,
        'player_b_id': player_b_id,
        'win_probability': {
            'player_a': win_prob['player_a_win_prob'],
            'player_b': win_prob['player_b_win_prob'],
            'confidence': win_prob['confidence'],
            'method': win_prob['method']
        },
        'head_to_head': {
            'total_matches': h2h['total_matches'],
            'player_a_wins': h2h['player_a_wins'],
            'player_b_wins': h2h['player_b_wins'],
            'last_5': h2h['last_5']
        },
        'form': {
            'player_a': {
                'last_10_win_pct': form_a.get('recent_win_pct'),
                'recent_opponent_avg_elo': form_a.get('avg_opponent_elo')
            },
            'player_b': {
                'last_10_win_pct': form_b.get('recent_win_pct'),
                'recent_opponent_avg_elo': form_b.get('avg_opponent_elo')
            }
        },
        'surface_stats': surface_comparison,
        'elo_trends': elo_trends
    }


def export_elo_rankings(features: dict, top_n: int = 100) -> dict:
    """
    Export Elo rankings.
    
    Args:
        features: Dictionary with computed features
        top_n: Number of top players to include
        
    Returns:
        Rankings dictionary
    """
    elo_system = features['elo_system']
    player_summaries = features['player_summaries']
    
    # Create rankings list
    rankings = []
    for player_summary in player_summaries:
        if player_summary['matches_played'] >= 10:  # Minimum matches
            rankings.append({
                'rank': None,  # Will be set after sorting
                'player_id': player_summary['id'],
                'name': player_summary['name'],
                'elo': player_summary['current_elo']
            })
    
    # Sort by Elo
    rankings.sort(key=lambda x: x['elo'], reverse=True)
    
    # Add ranks and limit to top N
    for i, player in enumerate(rankings[:top_n]):
        player['rank'] = i + 1
    
    return {
        'rankings': rankings[:top_n],
        'last_updated': datetime.now().isoformat() + 'Z'
    }


def main():
    """Main export function."""
    print("Starting data export pipeline...")
    
    # Load processed data or build features
    matches_path = os.path.join(DATA_RAW_DIR, "matches_combined.csv")
    if not os.path.exists(matches_path):
        print(f"Error: {matches_path} not found. Run ingest_sackmann.py first.")
        return
    
    matches_df = pd.read_csv(matches_path)
    matches_df['tourney_date'] = pd.to_datetime(matches_df['tourney_date'])
    
    # Build features
    print("Building features...")
    features = build_all_features(matches_df)
    
    # Create outputs directory
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    
    # Export player summary
    print("Exporting player summary...")
    player_summary = export_player_summary(features)
    with open(os.path.join(OUTPUTS_DIR, 'player_summary.json'), 'w') as f:
        json.dump(player_summary, f, indent=2)
    
    # Export Elo rankings
    print("Exporting Elo rankings...")
    rankings = export_elo_rankings(features)
    with open(os.path.join(OUTPUTS_DIR, 'elo_rankings.json'), 'w') as f:
        json.dump(rankings, f, indent=2)
    
    # Note: matchup_stats.json would be generated on-demand by the frontend
    # For now, create a sample or leave it empty
    print("Export complete!")
    print(f"Files saved to {OUTPUTS_DIR}/")


if __name__ == "__main__":
    main()
