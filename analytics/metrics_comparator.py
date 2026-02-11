"""
Metrics comparison utilities for player matchups.
"""
from typing import Dict, List, Tuple, Optional
from analytics.config import METRIC_WEIGHTS


class MetricsComparator:
    """Handles comparison of player metrics for win probability calculation."""
    
    @staticmethod
    def safe_value(val: Optional[float]) -> float:
        """
        Convert None to 0.0 for missing metrics.
        
        Args:
            val: Value that may be None
            
        Returns:
            Float value (0.0 if None)
        """
        return 0.0 if val is None else float(val)
    
    @staticmethod
    def compare_higher_is_better(
        value_a: float,
        value_b: float,
        metric_name: str,
        weight: float,
        format_str: Optional[str] = None
    ) -> Tuple[float, str, Dict]:
        """
        Compare two metrics where higher value is better.
        
        Args:
            value_a: Player A's metric value
            value_b: Player B's metric value
            metric_name: Name of the metric
            weight: Weight for this metric
            format_str: Optional format string for advantage message
            
        Returns:
            Tuple of (score, advantage, comparison_dict)
        """
        if value_a > value_b:
            score = weight
            advantage = 'player_a'
            advantage_msg = (
                format_str.format(player='A', value_a=value_a, value_b=value_b)
                if format_str else None
            )
        elif value_b > value_a:
            score = -weight
            advantage = 'player_b'
            advantage_msg = (
                format_str.format(player='B', value_a=value_b, value_b=value_a)
                if format_str else None
            )
        else:
            score = 0.0
            advantage = 'neutral'
            advantage_msg = None
        
        comparison = {
            'player_a': value_a,
            'player_b': value_b,
            'advantage': advantage
        }
        
        return score, advantage, comparison, advantage_msg
    
    @staticmethod
    def compare_lower_is_better(
        value_a: float,
        value_b: float,
        metric_name: str,
        weight: float,
        format_str: Optional[str] = None
    ) -> Tuple[float, str, Dict, Optional[str]]:
        """
        Compare two metrics where lower value is better.
        
        Args:
            value_a: Player A's metric value
            value_b: Player B's metric value
            metric_name: Name of the metric
            weight: Weight for this metric
            format_str: Optional format string for advantage message
            
        Returns:
            Tuple of (score, advantage, comparison_dict, advantage_msg)
        """
        if value_a < value_b:
            score = weight
            advantage = 'player_a'
            advantage_msg = (
                format_str.format(player='A', value_a=value_a, value_b=value_b)
                if format_str else None
            )
        elif value_b < value_a:
            score = -weight
            advantage = 'player_b'
            advantage_msg = (
                format_str.format(player='B', value_a=value_b, value_b=value_a)
                if format_str else None
            )
        else:
            score = 0.0
            advantage = 'neutral'
            advantage_msg = None
        
        comparison = {
            'player_a': value_a,
            'player_b': value_b,
            'advantage': advantage
        }
        
        return score, advantage, comparison, advantage_msg
    
    @staticmethod
    def compare_all_metrics(
        metrics_a: Dict,
        metrics_b: Dict,
        surface: Optional[str] = None
    ) -> Dict:
        """
        Compare all detailed metrics between two players.
        
        Args:
            metrics_a: Player A's detailed metrics dictionary
            metrics_b: Player B's detailed metrics dictionary
            surface: Optional surface for surface-specific comparison
            
        Returns:
            Dictionary with comparison results and scores
        """
        comparison = {}
        metric_scores = []
        key_advantages = []
        
        safe_val = MetricsComparator.safe_value
        
        # 1. Average winning margin (higher is better)
        margin_a = safe_val(metrics_a.get('avg_winning_margin'))
        margin_b = safe_val(metrics_b.get('avg_winning_margin'))
        score, adv, comp, msg = MetricsComparator.compare_higher_is_better(
            margin_a, margin_b, 'avg_winning_margin',
            METRIC_WEIGHTS['avg_winning_margin'],
            "Player {player} has larger winning margin ({value_a:.1f} vs {value_b:.1f} games)"
        )
        comparison['avg_winning_margin'] = comp
        metric_scores.append(score)
        if msg:
            key_advantages.append(msg)
        
        # 2. First set win percentage (higher is better)
        first_set_a = safe_val(metrics_a.get('first_set_win_pct'))
        first_set_b = safe_val(metrics_b.get('first_set_win_pct'))
        score, adv, comp, msg = MetricsComparator.compare_higher_is_better(
            first_set_a, first_set_b, 'first_set_win_pct',
            METRIC_WEIGHTS['first_set_win_pct'],
            "Player {player} wins first set more often ({value_a:.1%} vs {value_b:.1%})"
        )
        comparison['first_set_win_pct'] = comp
        metric_scores.append(score)
        if msg:
            key_advantages.append(msg)
        
        # 3. Second set win percentage (higher is better)
        second_set_a = safe_val(metrics_a.get('second_set_win_pct'))
        second_set_b = safe_val(metrics_b.get('second_set_win_pct'))
        score, adv, comp, msg = MetricsComparator.compare_higher_is_better(
            second_set_a, second_set_b, 'second_set_win_pct',
            METRIC_WEIGHTS['second_set_win_pct']
        )
        comparison['second_set_win_pct'] = comp
        metric_scores.append(score)
        
        # 4. Ace percentage (higher is better)
        ace_a = safe_val(metrics_a.get('ace_pct'))
        ace_b = safe_val(metrics_b.get('ace_pct'))
        score, adv, comp, msg = MetricsComparator.compare_higher_is_better(
            ace_a, ace_b, 'ace_pct',
            METRIC_WEIGHTS['ace_pct'],
            "Player {player} has stronger serve ({value_a:.1f}% vs {value_b:.1f}% ace rate)"
        )
        comparison['ace_pct'] = comp
        metric_scores.append(score)
        if msg:
            key_advantages.append(msg)
        
        # 5. Average minutes for wins (lower is better)
        minutes_win_a = safe_val(metrics_a.get('avg_minutes_for_wins'))
        minutes_win_b = safe_val(metrics_b.get('avg_minutes_for_wins'))
        if minutes_win_a > 0 and minutes_win_b > 0:
            score, adv, comp, msg = MetricsComparator.compare_lower_is_better(
                minutes_win_a, minutes_win_b, 'avg_minutes_for_wins',
                METRIC_WEIGHTS['avg_minutes_for_wins']
            )
        else:
            score, adv, comp, msg = 0.0, 'neutral', {
                'player_a': minutes_win_a,
                'player_b': minutes_win_b,
                'advantage': 'neutral'
            }, None
        comparison['avg_minutes_for_wins'] = comp
        metric_scores.append(score)
        
        # 6. Average losing game time (lower is better)
        minutes_loss_a = safe_val(metrics_a.get('avg_losing_game_time'))
        minutes_loss_b = safe_val(metrics_b.get('avg_losing_game_time'))
        if minutes_loss_a > 0 and minutes_loss_b > 0:
            score, adv, comp, msg = MetricsComparator.compare_lower_is_better(
                minutes_loss_a, minutes_loss_b, 'avg_losing_game_time',
                METRIC_WEIGHTS['avg_losing_game_time']
            )
        else:
            score, adv, comp, msg = 0.0, 'neutral', {
                'player_a': minutes_loss_a,
                'player_b': minutes_loss_b,
                'advantage': 'neutral'
            }, None
        comparison['avg_losing_game_time'] = comp
        metric_scores.append(score)
        
        # 7. Average opponent age when won (contextual)
        age_won_a = safe_val(metrics_a.get('avg_opponent_age_when_won'))
        age_won_b = safe_val(metrics_b.get('avg_opponent_age_when_won'))
        if age_won_a > 0 and age_won_b > 0:
            # Higher age when won might indicate tougher opponents beaten
            score, adv, comp, msg = MetricsComparator.compare_higher_is_better(
                age_won_a, age_won_b, 'avg_opponent_age_when_won',
                METRIC_WEIGHTS['avg_opponent_age_when_won'] * 0.5
            )
        else:
            score, adv, comp, msg = 0.0, 'neutral', {
                'player_a': age_won_a,
                'player_b': age_won_b,
                'advantage': 'neutral'
            }, None
        comparison['avg_opponent_age_when_won'] = comp
        metric_scores.append(score)
        
        # 8. Average opponent age when lost (contextual)
        age_lost_a = safe_val(metrics_a.get('avg_opponent_age_when_lost'))
        age_lost_b = safe_val(metrics_b.get('avg_opponent_age_when_lost'))
        if age_lost_a > 0 and age_lost_b > 0:
            # Lower age when lost might indicate losing to younger/stronger opponents
            score, adv, comp, msg = MetricsComparator.compare_lower_is_better(
                age_lost_a, age_lost_b, 'avg_opponent_age_when_lost',
                METRIC_WEIGHTS['avg_opponent_age_when_lost'] * 0.5
            )
        else:
            score, adv, comp, msg = 0.0, 'neutral', {
                'player_a': age_lost_a,
                'player_b': age_lost_b,
                'advantage': 'neutral'
            }, None
        comparison['avg_opponent_age_when_lost'] = comp
        metric_scores.append(score)
        
        # 9. Form: Last 10 wins (higher is better)
        form_10_a = safe_val(metrics_a.get('form_last_10_wins'))
        form_10_b = safe_val(metrics_b.get('form_last_10_wins'))
        score, adv, comp, msg = MetricsComparator.compare_higher_is_better(
            form_10_a, form_10_b, 'form_last_10_wins',
            METRIC_WEIGHTS['form_last_10_wins'],
            "Player {player} in better form (last 10 wins: {value_a:.1f} vs {value_b:.1f} avg margin)"
        )
        comparison['form_last_10_wins'] = comp
        metric_scores.append(score)
        if msg:
            key_advantages.append(msg)
        
        # 10. Form: Last 5 wins (higher is better)
        form_5_a = safe_val(metrics_a.get('form_last_5_wins'))
        form_5_b = safe_val(metrics_b.get('form_last_5_wins'))
        score, adv, comp, msg = MetricsComparator.compare_higher_is_better(
            form_5_a, form_5_b, 'form_last_5_wins',
            METRIC_WEIGHTS['form_last_5_wins'],
            "Player {player} in hot form (last 5 wins: {value_a:.1f} vs {value_b:.1f} avg margin)"
        )
        comparison['form_last_5_wins'] = comp
        metric_scores.append(score)
        if msg:
            key_advantages.append(msg)
        
        # 11. Surface match (check if playing on player's weak surface)
        surface_score = 0.0
        most_lost_a = metrics_a.get('most_lost_surface')
        most_lost_b = metrics_b.get('most_lost_surface')
        
        if surface:
            if most_lost_a == surface:
                surface_score -= METRIC_WEIGHTS['surface_match'] * 0.5
            if most_lost_b == surface:
                surface_score += METRIC_WEIGHTS['surface_match'] * 0.5
        
        comparison['surface_match'] = {
            'surface': surface,
            'player_a_weak_surface': most_lost_a,
            'player_b_weak_surface': most_lost_b,
            'advantage': 'player_a' if surface_score > 0 else ('player_b' if surface_score < 0 else 'neutral')
        }
        metric_scores.append(surface_score)
        
        # Calculate total score and convert to probability
        total_score = sum(metric_scores)
        non_zero_metrics = sum(1 for score in metric_scores if score != 0)
        
        # Convert score to probability using sigmoid transformation
        import numpy as np
        metric_prob_a = 1 / (1 + np.exp(-total_score * 2))
        metric_prob_b = 1 - metric_prob_a
        
        return {
            'metric_comparison': comparison,
            'metric_score': {
                'player_a': round(total_score, 3),
                'player_b': round(-total_score, 3)
            },
            'metric_probability': {
                'player_a': round(metric_prob_a, 3),
                'player_b': round(metric_prob_b, 3)
            },
            'key_advantages': key_advantages[:5],  # Top 5 advantages
            'metrics_available': non_zero_metrics,
            'total_metrics': len(metric_scores)
        }
