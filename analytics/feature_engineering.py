"""
Feature engineering for tennis match analysis.
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from analytics.utils import calculate_win_percentage, get_recent_matches
from analytics.config import (
    MIN_MATCHES_FOR_STATS,
    MIN_MATCHES_FOR_SURFACE_STATS,
    RECENT_FORM_MATCHES,
    RECENT_FORM_DAYS
)


class FeatureEngineer:
    """Computes features for tennis match analysis."""
    
    def __init__(self, matches_df: pd.DataFrame):
        """
        Initialize feature engineer with match data.
        
        Args:
            matches_df: DataFrame with match data
        """
        self.matches_df = matches_df.copy()
        if 'tourney_date' in self.matches_df.columns:
            self.matches_df['tourney_date'] = pd.to_datetime(self.matches_df['tourney_date'])
    
    def get_career_stats(self, player_id: str) -> Dict[str, Optional[float]]:
        """
        Get career statistics for a player.
        
        Args:
            player_id: Player identifier
            
        Returns:
            Dictionary with career stats
        """
        player_matches = self.matches_df[
            (self.matches_df['winner_id'] == player_id) | 
            (self.matches_df['loser_id'] == player_id)
        ]
        
        wins = len(player_matches[player_matches['winner_id'] == player_id])
        losses = len(player_matches[player_matches['loser_id'] == player_id])
        
        return {
            'career_wins': wins,
            'career_losses': losses,
            'career_win_pct': calculate_win_percentage(wins, losses, MIN_MATCHES_FOR_STATS),
            'total_matches': wins + losses
        }
    
    def get_recent_form(self, player_id: str, n_matches: int = RECENT_FORM_MATCHES) -> Dict[str, Optional[float]]:
        """
        Get recent form statistics.
        
        Args:
            player_id: Player identifier
            n_matches: Number of recent matches to consider
            
        Returns:
            Dictionary with recent form stats
        """
        player_matches = self.matches_df[
            (self.matches_df['winner_id'] == player_id) | 
            (self.matches_df['loser_id'] == player_id)
        ].sort_values('tourney_date', ascending=False).head(n_matches)
        
        if len(player_matches) == 0:
            return {
                'recent_wins': 0,
                'recent_losses': 0,
                'recent_win_pct': None,
                'recent_matches': 0
            }
        
        wins = len(player_matches[player_matches['winner_id'] == player_id])
        losses = len(player_matches[player_matches['loser_id'] == player_id])
        
        # Calculate average opponent strength (using Elo if available)
        recent_opponent_elos = []
        for _, match in player_matches.iterrows():
            opponent_id = match['loser_id'] if match['winner_id'] == player_id else match['winner_id']
            # This would need Elo ratings - placeholder for now
            recent_opponent_elos.append(1500)  # Default
        
        avg_opponent_elo = np.mean(recent_opponent_elos) if recent_opponent_elos else None
        
        return {
            'recent_wins': wins,
            'recent_losses': losses,
            'recent_win_pct': calculate_win_percentage(wins, losses, min_matches=1),
            'recent_matches': len(player_matches),
            'avg_opponent_elo': avg_opponent_elo
        }
    
    def get_surface_stats(self, player_id: str) -> Dict[str, Dict[str, Optional[float]]]:
        """
        Get surface-specific statistics.
        
        Args:
            player_id: Player identifier
            
        Returns:
            Dictionary mapping surface to stats
        """
        player_matches = self.matches_df[
            (self.matches_df['winner_id'] == player_id) | 
            (self.matches_df['loser_id'] == player_id)
        ]
        
        surface_stats = {}
        surfaces = ['Hard', 'Clay', 'Grass', 'Carpet']
        
        for surface in surfaces:
            surface_matches = player_matches[player_matches['surface'] == surface]
            if len(surface_matches) == 0:
                surface_stats[surface] = {
                    'wins': 0,
                    'losses': 0,
                    'win_pct': None,
                    'matches': 0
                }
                continue
            
            wins = len(surface_matches[surface_matches['winner_id'] == player_id])
            losses = len(surface_matches[surface_matches['loser_id'] == player_id])
            
            surface_stats[surface] = {
                'wins': wins,
                'losses': losses,
                'win_pct': calculate_win_percentage(
                    wins, losses, MIN_MATCHES_FOR_SURFACE_STATS
                ),
                'matches': wins + losses
            }
        
        return surface_stats
    
    def get_head_to_head(self, player_a_id: str, player_b_id: str) -> Dict:
        """
        Get head-to-head statistics between two players.
        
        Args:
            player_a_id: First player identifier
            player_b_id: Second player identifier
            
        Returns:
            Dictionary with H2H stats
        """
        h2h_matches = self.matches_df[
            ((self.matches_df['winner_id'] == player_a_id) & (self.matches_df['loser_id'] == player_b_id)) |
            ((self.matches_df['winner_id'] == player_b_id) & (self.matches_df['loser_id'] == player_a_id))
        ].sort_values('tourney_date', ascending=False)
        
        if len(h2h_matches) == 0:
            return {
                'total_matches': 0,
                'player_a_wins': 0,
                'player_b_wins': 0,
                'last_5': []
            }
        
        player_a_wins = len(h2h_matches[h2h_matches['winner_id'] == player_a_id])
        player_b_wins = len(h2h_matches[h2h_matches['winner_id'] == player_b_id])
        
        # Get last 5 meetings
        last_5 = []
        for _, match in h2h_matches.head(5).iterrows():
            last_5.append({
                'date': match['tourney_date'].strftime('%Y-%m-%d') if pd.notna(match['tourney_date']) else None,
                'winner': match['winner_id'],
                'loser': match['loser_id'],
                'surface': match.get('surface'),
                'score': match.get('score')
            })
        
        return {
            'total_matches': len(h2h_matches),
            'player_a_wins': player_a_wins,
            'player_b_wins': player_b_wins,
            'last_5': last_5
        }
    
    def get_tournament_performance(self, player_id: str) -> Dict[str, float]:
        """
        Get tournament-level performance statistics.
        
        Args:
            player_id: Player identifier
            
        Returns:
            Dictionary with tournament-level stats
        """
        player_matches = self.matches_df[
            (self.matches_df['winner_id'] == player_id) | 
            (self.matches_df['loser_id'] == player_id)
        ]
        
        tournament_stats = {}
        
        # Group by tournament level
        for level in ['G', 'M', '500', '250', 'A']:
            level_matches = player_matches[player_matches.get('tourney_level') == level]
            if len(level_matches) > 0:
                wins = len(level_matches[level_matches['winner_id'] == player_id])
                losses = len(level_matches[level_matches['loser_id'] == player_id])
                tournament_stats[level] = {
                    'win_pct': calculate_win_percentage(wins, losses, min_matches=1),
                    'matches': wins + losses
                }
        
        return tournament_stats
