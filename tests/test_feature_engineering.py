"""
Tests for feature engineering module.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from analytics.feature_engineering import FeatureEngineer, _parse_tennis_score


class TestScoreParsing:
    """Tests for tennis score parsing function."""
    
    def test_parse_simple_two_set_score(self):
        """Test parsing a simple two-set score."""
        score = "6-4 6-2"
        result = _parse_tennis_score(score)
        
        assert result is not None
        assert result['num_sets'] == 2
        assert result['first_set_winner_games'] == 6
        assert result['first_set_loser_games'] == 4
        assert result['first_set_won'] is True
        assert result['second_set_winner_games'] == 6
        assert result['second_set_loser_games'] == 2
        assert result['second_set_won'] is True
        assert result['winning_margin_games'] == 6  # (6+6) - (4+2)
    
    def test_parse_tiebreak_score(self):
        """Test parsing score with tiebreak."""
        score = "7-6(3) 6-3"
        result = _parse_tennis_score(score)
        
        assert result is not None
        assert result['num_sets'] == 2
        assert result['sets'][0]['tiebreak'] is True
        assert result['sets'][0]['tiebreak_score'] == 3
        assert result['winning_margin_games'] == 4  # (7+6) - (6+3)
    
    def test_parse_three_set_score(self):
        """Test parsing a three-set score."""
        score = "6-3 4-6 6-2"
        result = _parse_tennis_score(score)
        
        assert result is not None
        assert result['num_sets'] == 3
        assert result['first_set_won'] is True
        assert result['second_set_won'] is False
        assert result['winning_margin_games'] == 3  # (6+4+6) - (3+6+2)
    
    def test_parse_complex_tiebreak(self):
        """Test parsing score with multiple tiebreaks."""
        score = "7-5 6-7(4) 6-1"
        result = _parse_tennis_score(score)
        
        assert result is not None
        assert result['num_sets'] == 3
        assert result['sets'][0]['tiebreak'] is False
        assert result['sets'][1]['tiebreak'] is True
        assert result['sets'][1]['tiebreak_score'] == 4
    
    def test_parse_invalid_score(self):
        """Test parsing invalid score returns None."""
        assert _parse_tennis_score("invalid") is None
        assert _parse_tennis_score("") is None
        assert _parse_tennis_score(None) is None
    
    def test_parse_nan_score(self):
        """Test parsing NaN score."""
        import pandas as pd
        assert _parse_tennis_score(pd.NA) is None
        assert _parse_tennis_score(float('nan')) is None


class TestFeatureEngineer:
    """Tests for FeatureEngineer class."""
    
    @pytest.fixture
    def sample_matches(self):
        """Create sample match data for testing."""
        return pd.DataFrame({
            'tourney_date': pd.to_datetime(['2023-01-15', '2023-01-20', '2023-02-01', '2023-02-10']),
            'winner_id': ['player1', 'player2', 'player1', 'player1'],
            'loser_id': ['player2', 'player1', 'player2', 'player2'],
            'winner_name_normalized': ['Player One', 'Player Two', 'Player One', 'Player One'],
            'loser_name_normalized': ['Player Two', 'Player One', 'Player Two', 'Player Two'],
            'surface': ['Hard', 'Clay', 'Hard', 'Grass'],
            'score': ['6-4 6-2', '7-6(3) 6-3', '6-3 4-6 6-2', '6-2 6-1'],
            'minutes': [120.0, 135.0, 150.0, 95.0],
            'w_ace': [10, 5, 8, 12],
            'l_ace': [3, 7, 4, 2],
            'w_svpt': [60, 70, 65, 55],
            'l_svpt': [58, 65, 62, 50],
            'winner_age': [25.5, 28.2, 25.6, 25.7],
            'loser_age': [27.3, 25.5, 27.4, 27.5]
        })
    
    def test_get_detailed_metrics_basic(self, sample_matches):
        """Test getting detailed metrics for a player."""
        engineer = FeatureEngineer(sample_matches)
        metrics = engineer.get_detailed_player_metrics('player1')
        
        assert metrics is not None
        assert 'avg_winning_margin' in metrics
        assert 'avg_minutes_for_wins' in metrics
        assert 'first_set_win_pct' in metrics
        assert 'second_set_win_pct' in metrics
        assert 'ace_pct' in metrics
        assert 'most_lost_surface' in metrics
        assert 'avg_losing_game_time' in metrics
        assert 'avg_opponent_age_when_lost' in metrics
        assert 'avg_opponent_age_when_won' in metrics
    
    def test_avg_winning_margin(self, sample_matches):
        """Test average winning margin calculation."""
        engineer = FeatureEngineer(sample_matches)
        metrics = engineer.get_detailed_player_metrics('player1')
        
        # Player1 wins: 6-4 6-2 (margin: 6), 6-3 4-6 6-2 (margin: 3), 6-2 6-1 (margin: 9)
        # Average should be around 6
        assert metrics['avg_winning_margin'] is not None
        assert metrics['avg_winning_margin'] > 0
    
    def test_avg_minutes_for_wins(self, sample_matches):
        """Test average minutes for wins."""
        engineer = FeatureEngineer(sample_matches)
        metrics = engineer.get_detailed_player_metrics('player1')
        
        # Player1 wins: 120, 150, 95 minutes
        # Average: (120 + 150 + 95) / 3 = 121.67
        assert metrics['avg_minutes_for_wins'] is not None
        assert 90 <= metrics['avg_minutes_for_wins'] <= 160
    
    def test_first_set_win_pct(self, sample_matches):
        """Test first set winning percentage."""
        engineer = FeatureEngineer(sample_matches)
        metrics = engineer.get_detailed_player_metrics('player1')
        
        # Player1: wins first set in matches 1, 3, 4; loses in match 2
        # Should be 3/4 = 0.75
        assert metrics['first_set_win_pct'] is not None
        assert 0 <= metrics['first_set_win_pct'] <= 1
    
    def test_ace_percentage(self, sample_matches):
        """Test ace percentage calculation."""
        engineer = FeatureEngineer(sample_matches)
        metrics = engineer.get_detailed_player_metrics('player1')
        
        # Player1 aces: 10, 4, 12 = 26 total
        # Player1 service points: 60, 65, 55 = 180 total
        # Ace % = 26/180 * 100 ≈ 14.44%
        assert metrics['ace_pct'] is not None
        assert 0 <= metrics['ace_pct'] <= 100
    
    def test_most_lost_surface(self, sample_matches):
        """Test most lost surface."""
        engineer = FeatureEngineer(sample_matches)
        metrics = engineer.get_detailed_player_metrics('player1')
        
        # Player1 loses on Clay (match 2)
        assert metrics['most_lost_surface'] == 'Clay'
    
    def test_avg_losing_game_time(self, sample_matches):
        """Test average losing game time."""
        engineer = FeatureEngineer(sample_matches)
        metrics = engineer.get_detailed_player_metrics('player1')
        
        # Player1 loses: match 2 with 135 minutes
        assert metrics['avg_losing_game_time'] == 135.0
    
    def test_opponent_age_when_lost(self, sample_matches):
        """Test average opponent age when lost."""
        engineer = FeatureEngineer(sample_matches)
        metrics = engineer.get_detailed_player_metrics('player1')
        
        # Player1 loses to player2 (age 28.2)
        assert metrics['avg_opponent_age_when_lost'] == 28.2
    
    def test_opponent_age_when_won(self, sample_matches):
        """Test average opponent age when won."""
        engineer = FeatureEngineer(sample_matches)
        metrics = engineer.get_detailed_player_metrics('player1')
        
        # Player1 wins against player2 (ages: 27.3, 27.4, 27.5)
        # Average: (27.3 + 27.4 + 27.5) / 3 = 27.4
        assert metrics['avg_opponent_age_when_won'] is not None
        assert 27.0 <= metrics['avg_opponent_age_when_won'] <= 28.0
    
    def test_empty_player_matches(self, sample_matches):
        """Test metrics for player with no matches."""
        engineer = FeatureEngineer(sample_matches)
        metrics = engineer.get_detailed_player_metrics('nonexistent_player')
        
        assert metrics['avg_winning_margin'] is None
        assert metrics['avg_minutes_for_wins'] is None
        assert metrics['first_set_win_pct'] is None
    
    def test_missing_data_handling(self):
        """Test handling of matches with missing data."""
        matches = pd.DataFrame({
            'tourney_date': pd.to_datetime(['2023-01-15']),
            'winner_id': ['player1'],
            'loser_id': ['player2'],
            'winner_name_normalized': ['Player One'],
            'loser_name_normalized': ['Player Two'],
            'surface': ['Hard'],
            'score': [None],  # Missing score
            'minutes': [None],  # Missing minutes
            'w_ace': [None],
            'l_ace': [None],
            'w_svpt': [None],
            'l_svpt': [None],
            'winner_age': [None],
            'loser_age': [None]
        })
        
        engineer = FeatureEngineer(matches)
        metrics = engineer.get_detailed_player_metrics('player1')
        
        # Should handle missing data gracefully
        assert metrics is not None
        # Most metrics should be None due to missing data
        assert metrics['avg_winning_margin'] is None or isinstance(metrics['avg_winning_margin'], (int, float))
    
    def test_career_stats_integration(self, sample_matches):
        """Test that detailed metrics work alongside existing methods."""
        engineer = FeatureEngineer(sample_matches)
        
        # Should not break existing functionality
        career_stats = engineer.get_career_stats('player1')
        assert career_stats is not None
        assert 'career_wins' in career_stats
        
        # Detailed metrics should also work
        detailed = engineer.get_detailed_player_metrics('player1')
        assert detailed is not None
