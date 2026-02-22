"""
Export processed data to JSON for frontend consumption.

This pipeline exports analytics data in JSON format for the dashboard:
1. Player summaries (active players with rankings)
2. Elo rankings (top N players)
3. Matchup statistics (on-demand, not in main export)
"""
import json
import os
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from analytics.config import OUTPUTS_DIR, DATA_RAW_DIR, MIN_MATCHES_FOR_EXPORT
from analytics.elo import EloRating
from analytics.feature_engineering import FeatureEngineer
from analytics.win_probability import WinProbabilityCalculator
from pipelines.build_features import build_all_features


def _filter_active_players(
    player_summaries: List[Dict],
    min_matches: int = MIN_MATCHES_FOR_EXPORT
) -> List[Dict]:
    """
    Filter and sort players by Elo rating.
    
    Args:
        player_summaries: List of player summary dictionaries
        min_matches: Minimum matches required to be considered active
        
    Returns:
        List of active players sorted by Elo (descending)
    """
    active_players = [
        player for player in player_summaries
        if player.get('matches_played', 0) >= min_matches
    ]
    
    # Sort by Elo rating (descending)
    active_players.sort(key=lambda x: x.get('current_elo', 0), reverse=True)
    
    return active_players


def _add_rankings(players: List[Dict]) -> None:
    """
    Add ranking numbers to sorted player list (in-place).
    
    Args:
        players: List of player dictionaries (should be pre-sorted by Elo)
    """
    for rank, player in enumerate(players, start=1):
        player['current_rank'] = rank


def export_player_summary(features: Dict) -> Dict:
    """
    Export player summary data for dashboard.
    
    Filters to active players (minimum matches threshold) and includes
    Elo rankings and basic statistics.
    
    Args:
        features: Dictionary with computed features from build_all_features()
        
    Returns:
        Dictionary with players list and metadata
        
    Example:
        {
            'players': [
                {'id': '...', 'name': '...', 'current_elo': 1650, 'current_rank': 1, ...},
                ...
            ],
            'last_updated': '2024-01-01T00:00:00Z'
        }
    """
    player_summaries = features['player_summaries']
    
    # Filter and sort active players
    active_players = _filter_active_players(player_summaries)
    
    # Build export format
    players = []
    for player_summary in active_players:
        players.append({
            'id': player_summary['id'],
            'name': player_summary['name'],
            'current_elo': player_summary['current_elo'],
            'current_rank': None,  # Will be set below
            'career_win_pct': player_summary.get('career_win_pct'),
            'matches_played': player_summary.get('matches_played', 0),
            'detailed_metrics': player_summary.get('detailed_metrics', {}),
            'active': True  # All filtered players are considered active
        })
    
    # Add rankings
    _add_rankings(players)
    
    return {
        'players': players,
        'last_updated': datetime.now().isoformat() + 'Z'
    }


def _build_surface_comparison(
    surface_stats_a: Dict,
    surface_stats_b: Dict,
    surfaces: List[str] = ['Hard', 'Clay', 'Grass']
) -> Dict:
    """
    Build surface comparison dictionary for two players.
    
    Args:
        surface_stats_a: Player A's surface statistics
        surface_stats_b: Player B's surface statistics
        surfaces: List of surfaces to compare
        
    Returns:
        Dictionary mapping surface (lowercase) to win percentages
    """
    comparison = {}
    for surface_type in surfaces:
        comparison[surface_type.lower()] = {
            'player_a': surface_stats_a.get(surface_type, {}).get('win_pct'),
            'player_b': surface_stats_b.get(surface_type, {}).get('win_pct')
        }
    return comparison


def export_matchup_stats(
    player_a_id: str,
    player_b_id: str,
    features: Dict,
    surface: Optional[str] = 'Hard'
) -> Dict:
    """
    Export matchup statistics for two players.
    
    Calculates comprehensive comparison including:
    - Win probability (hybrid Elo + Metrics)
    - Head-to-head record
    - Recent form
    - Surface-specific statistics
    - Metric comparisons
    
    Args:
        player_a_id: First player ID
        player_b_id: Second player ID
        features: Dictionary with computed features from build_all_features()
        surface: Surface type for surface-specific calculations (default: 'Hard')
        
    Returns:
        Dictionary with complete matchup statistics
        
    Note:
        This function is typically called on-demand by the frontend,
        not during the main export pipeline.
    """
    elo_system = features['elo_system']
    feature_engineer = features['feature_engineer']
    
    # Calculate win probability using hybrid approach (Elo + Metrics)
    win_prob_calc = WinProbabilityCalculator(elo_system, feature_engineer)
    
    # Get H2H
    h2h = feature_engineer.get_head_to_head(player_a_id, player_b_id)
    
    # Calculate win probability
    win_prob = win_prob_calc.calculate_hybrid_probability(
        player_a_id, player_b_id, surface, h2h
    )
    
    # Get form for both players
    form_a = feature_engineer.get_recent_form(player_a_id)
    form_b = feature_engineer.get_recent_form(player_b_id)
    
    # Get surface stats
    surface_stats_a = feature_engineer.get_surface_stats(player_a_id)
    surface_stats_b = feature_engineer.get_surface_stats(player_b_id)
    
    # Build surface comparison
    surface_comparison = _build_surface_comparison(surface_stats_a, surface_stats_b)
    
    # Elo trends placeholder (would require historical Elo tracking)
    elo_trends = {
        'player_a': [],
        'player_b': []
    }
    
    return {
        'player_a_id': player_a_id,
        'player_b_id': player_b_id,
        'win_probability': {
            'player_a': win_prob['player_a_win_prob'],
            'player_b': win_prob['player_b_win_prob'],
            'confidence': win_prob['confidence'],
            'method': win_prob['method'],
            'elo_probability': win_prob.get('elo_probability'),
            'metric_probability': win_prob.get('metric_probability'),
            'key_advantages': win_prob.get('key_advantages', []),
            'metrics_available': win_prob.get('metrics_available', 0),
            'fallback_reason': win_prob.get('fallback_reason')
        },
        'metric_comparison': win_prob.get('metric_comparison'),
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


def export_elo_rankings(features: Dict, top_n: int = 100) -> Dict:
    """
    Export Elo rankings for top N players.
    
    Args:
        features: Dictionary with computed features from build_all_features()
        top_n: Number of top players to include (default: 100)
        
    Returns:
        Dictionary with rankings list and metadata
        
    Example:
        {
            'rankings': [
                {'rank': 1, 'player_id': '...', 'name': '...', 'elo': 1650},
                ...
            ],
            'last_updated': '2024-01-01T00:00:00Z'
        }
    """
    player_summaries = features['player_summaries']
    
    # Filter active players and sort by Elo
    active_players = _filter_active_players(player_summaries)
    
    # Build rankings list
    rankings = []
    for player_summary in active_players[:top_n]:
        rankings.append({
            'rank': None,  # Will be set below
            'player_id': player_summary['id'],
            'name': player_summary['name'],
            'elo': player_summary['current_elo']
        })
    
    # Add rankings
    _add_rankings(rankings)
    
    return {
        'rankings': rankings,
        'last_updated': datetime.now().isoformat() + 'Z'
    }


def _save_json(data: Dict, filepath: str) -> None:
    """
    Save dictionary to JSON file.
    
    Args:
        data: Dictionary to save
        filepath: Path to save JSON file
        
    Raises:
        IOError: If file writing fails
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise IOError(f"Failed to save JSON to {filepath}: {e}")


def _load_and_build_features() -> Dict:
    """
    Load match data and build all features.
    
    Returns:
        Dictionary with computed features
        
    Raises:
        FileNotFoundError: If match data file doesn't exist
        ValueError: If feature building fails
    """
    matches_path = os.path.join(DATA_RAW_DIR, "matches_combined.csv")
    
    if not os.path.exists(matches_path):
        raise FileNotFoundError(
            f"Match data file not found: {matches_path}\n"
            "Please run ingest_sackmann.py first to download and normalize data."
        )
    
    try:
        matches_df = pd.read_csv(matches_path)
        matches_df['tourney_date'] = pd.to_datetime(matches_df['tourney_date'], errors='coerce')
        
        print("Building features...")
        return build_all_features(matches_df)
    except Exception as e:
        raise ValueError(f"Failed to build features: {e}")


def main() -> None:
    """
    Main export function.
    
    Orchestrates the export pipeline:
    1. Loads match data and builds features
    2. Exports player summaries to JSON
    3. Exports Elo rankings to JSON
    
    Note:
        Matchup statistics are generated on-demand by the frontend,
        not during the main export.
    """
    print("=" * 60)
    print("Starting data export pipeline...")
    print("=" * 60)
    
    # Load data and build features
    try:
        features = _load_and_build_features()
    except (FileNotFoundError, ValueError) as e:
        print(f"✗ Error: {e}")
        return
    
    # Create outputs directory
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    
    # Export player summary
    try:
        print("Exporting player summary...")
        player_summary = export_player_summary(features)
        player_summary_path = os.path.join(OUTPUTS_DIR, 'player_summary.json')
        _save_json(player_summary, player_summary_path)
        print(f"✓ Exported {len(player_summary['players']):,} players")
        print(f"  Location: {player_summary_path}")
    except Exception as e:
        print(f"✗ Error exporting player summary: {e}")
        return
    
    # Export Elo rankings
    try:
        print("Exporting Elo rankings...")
        rankings = export_elo_rankings(features)
        rankings_path = os.path.join(OUTPUTS_DIR, 'elo_rankings.json')
        _save_json(rankings, rankings_path)
        print(f"✓ Exported {len(rankings['rankings']):,} rankings")
        print(f"  Location: {rankings_path}")
    except Exception as e:
        print(f"✗ Error exporting rankings: {e}")
        return
    
    print("=" * 60)
    print("Export complete!")
    print(f"Files saved to {OUTPUTS_DIR}/")
    print("=" * 60)
    print("\nNote: matchup_stats.json is generated on-demand by the frontend")


if __name__ == "__main__":
    main()
