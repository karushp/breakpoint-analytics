"""
Feature engineering for tennis match analysis.

This module provides the FeatureEngineer class for computing various
statistics and metrics from tennis match data.
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from analytics.utils import calculate_win_percentage, convert_to_native_type
from analytics.config import (
    MIN_MATCHES_FOR_STATS,
    MIN_MATCHES_FOR_SURFACE_STATS,
    RECENT_FORM_MATCHES,
    RECENT_FORM_DAYS
)
from analytics.score_parser import ScoreParser
from analytics.metrics_comparator import MetricsComparator


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
        player_matches = self._get_player_matches(player_id)
        wins, losses = self._calculate_wins_losses(player_matches, player_id)
        
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
        player_matches = self._get_player_matches(player_id)
        recent_matches = player_matches.sort_values('tourney_date', ascending=False).head(n_matches)
        
        if len(recent_matches) == 0:
            return {
                'recent_wins': 0,
                'recent_losses': 0,
                'recent_win_pct': None,
                'recent_matches': 0,
                'avg_opponent_elo': None
            }
        
        wins, losses = self._calculate_wins_losses(recent_matches, player_id)
        
        # Note: avg_opponent_elo calculation would require Elo system integration
        # Currently returns None as placeholder for future enhancement
        return {
            'recent_wins': wins,
            'recent_losses': losses,
            'recent_win_pct': calculate_win_percentage(wins, losses, min_matches=1),
            'recent_matches': len(recent_matches),
            'avg_opponent_elo': None  # Placeholder - would need Elo system
        }
    
    def get_latest_game_info(
        self,
        player_id: str,
        reference_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get the player's most recent match: date, whether they won, and days ago.
        
        Used for recency bonus: if latest game is within last N days and a win,
        the player can receive a small boost in win probability.
        
        Args:
            player_id: Player identifier
            reference_date: Date to measure "days ago" from (default: latest date in data)
            
        Returns:
            Dict with 'date', 'is_win', 'days_ago' (None if no matches)
        """
        player_matches = self._get_player_matches(player_id)
        if len(player_matches) == 0:
            return {'date': None, 'is_win': None, 'days_ago': None}
        
        latest = player_matches.sort_values('tourney_date', ascending=False).iloc[0]
        match_date = latest['tourney_date']
        if pd.isna(match_date):
            return {'date': None, 'is_win': None, 'days_ago': None}
        # Ensure we have a date-like for subtraction
        if hasattr(match_date, 'to_pydatetime'):
            match_date = match_date.to_pydatetime()
        if reference_date is None:
            ref = self.matches_df['tourney_date'].max()
            if hasattr(ref, 'to_pydatetime'):
                ref = ref.to_pydatetime()
            reference_date = ref
        days_ago = (reference_date - match_date).days
        is_win = latest['winner_id'] == player_id
        return {
            'date': match_date,
            'is_win': bool(is_win),
            'days_ago': days_ago
        }
    
    def get_surface_stats(self, player_id: str) -> Dict[str, Dict[str, Optional[float]]]:
        """
        Get surface-specific statistics.
        
        Args:
            player_id: Player identifier
            
        Returns:
            Dictionary mapping surface to stats
        """
        player_matches = self._get_player_matches(player_id)
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
            
            wins, losses = self._calculate_wins_losses(surface_matches, player_id)
            
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
    
    def get_tournament_performance(self, player_id: str) -> Dict[str, Dict[str, Optional[float]]]:
        """
        Get tournament-level performance statistics.
        
        Note: Currently not used in main pipeline but available for future features.
        
        Args:
            player_id: Player identifier
            
        Returns:
            Dictionary with tournament-level stats
        """
        player_matches = self._get_player_matches(player_id)
        tournament_stats = {}
        
        # Group by tournament level
        for level in ['G', 'M', '500', '250', 'A']:
            level_matches = player_matches[player_matches.get('tourney_level') == level]
            if len(level_matches) > 0:
                wins, losses = self._calculate_wins_losses(level_matches, player_id)
                tournament_stats[level] = {
                    'win_pct': calculate_win_percentage(wins, losses, min_matches=1),
                    'matches': wins + losses
                }
        
        return tournament_stats
    
    def get_detailed_player_metrics(self, player_id: str) -> Dict[str, Optional[float]]:
        """
        Get detailed performance metrics for a player.
        
        Includes:
        - Average winning margin (in games)
        - Average minutes for wins
        - First set winning percentage
        - Second set winning percentage
        - Ace percentage
        - Most lost surface
        - Average losing game time
        - Average age of opponent when lost
        - Average age of opponent when won
        
        Args:
            player_id: Player identifier
            
        Returns:
            Dictionary with detailed metrics
        """
        player_matches = self._get_player_matches(player_id).copy()
        
        if len(player_matches) == 0:
            return {
                'avg_winning_margin': None,
                'avg_minutes_for_wins': None,
                'first_set_win_pct': None,
                'second_set_win_pct': None,
                'ace_pct': None,
                'most_lost_surface': None,
                'avg_losing_game_time': None,
                'avg_opponent_age_when_lost': None,
                'avg_opponent_age_when_won': None,
                'form_last_10_wins': None,
                'form_last_5_wins': None
            }
        
        # Separate wins and losses
        wins = player_matches[player_matches['winner_id'] == player_id].copy()
        losses = player_matches[player_matches['loser_id'] == player_id].copy()
        
        # 1. Average winning margin
        avg_winning_margin = self._calculate_avg_winning_margin(wins)
        
        # Form metrics: Average winning margin from recent wins
        form_last_10_wins = self._calculate_form_metric(wins, n_wins=10)
        form_last_5_wins = self._calculate_form_metric(wins, n_wins=5)
        
        # 2. Average minutes for wins
        win_minutes = wins['minutes'].dropna()
        avg_minutes_for_wins = win_minutes.mean() if len(win_minutes) > 0 else None
        
        # 3. First set winning percentage
        first_set_win_pct = self._calculate_set_win_pct(player_matches, player_id, set_number=1)
        
        # 4. Second set winning percentage
        second_set_win_pct = self._calculate_set_win_pct(player_matches, player_id, set_number=2)
        
        # 5. Ace percentage (total aces / total service points across all matches)
        total_aces = 0
        total_service_points = 0
        
        for _, match in player_matches.iterrows():
            is_winner = match['winner_id'] == player_id
            if is_winner:
                aces = match.get('w_ace', 0)
                svpt = match.get('w_svpt', 0)
            else:
                aces = match.get('l_ace', 0)
                svpt = match.get('l_svpt', 0)
            
            if pd.notna(aces) and pd.notna(svpt) and svpt > 0:
                total_aces += aces
                total_service_points += svpt
        
        ace_pct = (total_aces / total_service_points * 100) if total_service_points > 0 else None
        
        # 6. Most lost surface
        if len(losses) > 0:
            surface_losses = losses['surface'].value_counts()
            most_lost_surface = surface_losses.index[0] if len(surface_losses) > 0 else None
        else:
            most_lost_surface = None
        
        # 7. Average losing game time
        loss_minutes = losses['minutes'].dropna()
        avg_losing_game_time = loss_minutes.mean() if len(loss_minutes) > 0 else None
        
        # 8. Average age of opponent when lost
        opponent_ages_when_lost = []
        for _, match in losses.iterrows():
            opponent_age = match.get('winner_age')
            if pd.notna(opponent_age):
                opponent_ages_when_lost.append(opponent_age)
        
        avg_opponent_age_when_lost = np.mean(opponent_ages_when_lost) if opponent_ages_when_lost else None
        
        # 9. Average age of opponent when won
        opponent_ages_when_won = []
        for _, match in wins.iterrows():
            opponent_age = match.get('loser_age')
            if pd.notna(opponent_age):
                opponent_ages_when_won.append(opponent_age)
        
        avg_opponent_age_when_won = np.mean(opponent_ages_when_won) if opponent_ages_when_won else None
        
        return {
            'avg_winning_margin': convert_to_native_type(round(avg_winning_margin, 2) if avg_winning_margin is not None else None),
            'avg_minutes_for_wins': convert_to_native_type(round(avg_minutes_for_wins, 1) if avg_minutes_for_wins is not None else None),
            'first_set_win_pct': convert_to_native_type(round(first_set_win_pct, 3) if first_set_win_pct is not None else None),
            'second_set_win_pct': convert_to_native_type(round(second_set_win_pct, 3) if second_set_win_pct is not None else None),
            'ace_pct': convert_to_native_type(round(ace_pct, 2) if ace_pct is not None else None),
            'most_lost_surface': most_lost_surface,
            'avg_losing_game_time': convert_to_native_type(round(avg_losing_game_time, 1) if avg_losing_game_time is not None else None),
            'avg_opponent_age_when_lost': convert_to_native_type(round(avg_opponent_age_when_lost, 1) if avg_opponent_age_when_lost is not None else None),
            'avg_opponent_age_when_won': convert_to_native_type(round(avg_opponent_age_when_won, 1) if avg_opponent_age_when_won is not None else None),
            'form_last_10_wins': convert_to_native_type(round(form_last_10_wins, 2) if form_last_10_wins is not None else None),
            'form_last_5_wins': convert_to_native_type(round(form_last_5_wins, 2) if form_last_5_wins is not None else None)
        }
    
    def compare_detailed_metrics(
        self,
        player_a_id: str,
        player_b_id: str,
        surface: Optional[str] = None
    ) -> Dict:
        """
        Compare detailed metrics between two players.
        
        Args:
            player_a_id: First player identifier
            player_b_id: Second player identifier
            surface: Optional surface for surface-specific comparison
            
        Returns:
            Dictionary with metric comparison and scores
        """
        metrics_a = self.get_detailed_player_metrics(player_a_id)
        metrics_b = self.get_detailed_player_metrics(player_b_id)
        
        return MetricsComparator.compare_all_metrics(metrics_a, metrics_b, surface)
    
    # Helper methods for detailed metrics calculation
    
    def _calculate_avg_winning_margin(self, wins: pd.DataFrame) -> Optional[float]:
        """Calculate average winning margin from wins DataFrame."""
        winning_margins = []
        for _, match in wins.iterrows():
            if pd.notna(match.get('score')):
                parsed = ScoreParser.parse(match['score'])
                if parsed:
                    winning_margins.append(parsed['winning_margin_games'])
        return np.mean(winning_margins) if winning_margins else None
    
    def _calculate_set_win_pct(
        self,
        player_matches: pd.DataFrame,
        player_id: str,
        set_number: int
    ) -> Optional[float]:
        """
        Calculate set winning percentage for a specific set.
        
        Args:
            player_matches: DataFrame of player's matches
            player_id: Player identifier
            set_number: Set number (1 or 2)
            
        Returns:
            Set winning percentage or None
        """
        set_wins = 0
        set_total = 0
        set_key = 'first_set_won' if set_number == 1 else 'second_set_won'
        
        for _, match in player_matches.iterrows():
            if pd.notna(match.get('score')):
                parsed = ScoreParser.parse(match['score'])
                if parsed and parsed.get(set_key) is not None:
                    set_total += 1
                    is_winner = match['winner_id'] == player_id
                    if (is_winner and parsed[set_key]) or (not is_winner and not parsed[set_key]):
                        set_wins += 1
        
        return (set_wins / set_total) if set_total > 0 else None
    
    def _calculate_form_metric(self, wins: pd.DataFrame, n_wins: int) -> Optional[float]:
        """
        Calculate form metric: average winning margin from last N wins.
        
        Args:
            wins: DataFrame of player's wins
            n_wins: Number of recent wins to consider
            
        Returns:
            Average winning margin or None
        """
        wins_sorted = wins.sort_values('tourney_date', ascending=False)
        form_margins = []
        
        for _, match in wins_sorted.head(n_wins).iterrows():
            if pd.notna(match.get('score')):
                parsed = ScoreParser.parse(match['score'])
                if parsed:
                    form_margins.append(parsed['winning_margin_games'])
        
        return np.mean(form_margins) if form_margins else None
    
    # Helper methods for common patterns
    
    def _get_player_matches(self, player_id: str) -> pd.DataFrame:
        """
        Get all matches for a player (as winner or loser).
        
        Args:
            player_id: Player identifier
            
        Returns:
            DataFrame with player's matches
        """
        return self.matches_df[
            (self.matches_df['winner_id'] == player_id) | 
            (self.matches_df['loser_id'] == player_id)
        ]
    
    def _calculate_wins_losses(
        self,
        matches: pd.DataFrame,
        player_id: str
    ) -> Tuple[int, int]:
        """
        Calculate wins and losses from a matches DataFrame.
        
        Args:
            matches: DataFrame of matches
            player_id: Player identifier
            
        Returns:
            Tuple of (wins, losses)
        """
        wins = len(matches[matches['winner_id'] == player_id])
        losses = len(matches[matches['loser_id'] == player_id])
        return wins, losses
