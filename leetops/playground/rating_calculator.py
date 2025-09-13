"""
LeetOps Rating Calculation System
Implements the standardized rating algorithm for on-call engineering performance
"""

import math
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta


class RatingCalculator:
    """
    Calculates LeetOps ratings based on incident resolution performance
    Rating Scale: 800-1600 (SAT-style scoring)
    """
    
    # Base rating for new users
    BASE_RATING = 800
    
    # Rating categories
    RATING_CATEGORIES = {
        "junior": (800, 999),      # Junior level reliability
        "mid": (1000, 1199),       # Mid-level on-call ready  
        "senior": (1200, 1399),    # Senior incident responder
        "staff": (1400, 1600)      # Staff+ level crisis manager
    }
    
    # Speed bonus multipliers (based on % of time limit used)
    SPEED_BONUSES = {
        "excellent": (0, 0.25, 50),    # < 25% of time limit: +50 points
        "good": (0.25, 0.50, 30),      # < 50% of time limit: +30 points
        "satisfactory": (0.50, 0.75, 15), # < 75% of time limit: +15 points
        "adequate": (0.75, 1.00, 5),   # Within time limit: +5 points
        "poor": (1.00, float('inf'), 0) # Over time limit: 0 points
    }
    
    # Quality multipliers
    QUALITY_MULTIPLIERS = {
        "root_cause": 2.0,      # Root cause fix: 2x multiplier
        "workaround": 1.0,      # Temporary workaround: 1x multiplier
        "escalation": 0.5,      # Escalated to senior: 0.5x multiplier
        "abandonment": 0.0      # Gave up: 0x multiplier
    }
    
    # Penalties
    PENALTIES = {
        "give_up": -20,         # Give up: -20 points
        "timeout": -10,         # Timeout without solution: -10 points
        "escalation": -5        # Escalation (minor penalty): -5 points
    }
    
    # Severity weights (higher severity = more points available)
    SEVERITY_WEIGHTS = {
        "P0": 100,  # Critical incidents worth more points
        "P1": 75,   # High severity
        "P2": 50,   # Medium severity  
        "P3": 25    # Low severity
    }
    
    @classmethod
    def calculate_rating_with_groq_score(
        cls,
        llm_score: int,
        time_spent_minutes: int,
        time_limit_minutes: int,
        severity: str
    ) -> Dict[str, Any]:
        """
        Calculate rating change based on Groq LLM score and time factors
        
        Args:
            llm_score: Score from Groq LLM (0-100)
            time_spent_minutes: Time taken to resolve
            time_limit_minutes: Time limit for resolution
            severity: Incident severity (P0, P1, P2, P3)
            
        Returns:
            Dict containing rating calculation details
        """
        
        # Base rating change based on LLM score
        if llm_score >= 80:
            # High quality answer - high increase
            base_rating_change = 25
        elif llm_score >= 50:
            # Medium quality answer - mid increase  
            base_rating_change = 10
        else:
            # Poor answer - deduction regardless of time
            base_rating_change = -15
        
        # Time efficiency multiplier
        if time_limit_minutes > 0:
            time_ratio = time_spent_minutes / time_limit_minutes
            
            if llm_score >= 80:
                # For high quality answers, reward speed
                if time_ratio <= 0.5:
                    time_multiplier = 1.5  # Very fast + high quality = bonus
                elif time_ratio <= 0.75:
                    time_multiplier = 1.2  # Fast + high quality = good bonus
                else:
                    time_multiplier = 1.0  # Normal time + high quality = base
            elif llm_score >= 50:
                # For medium quality answers, moderate time impact
                if time_ratio <= 0.5:
                    time_multiplier = 1.2  # Fast + medium quality = small bonus
                elif time_ratio <= 0.75:
                    time_multiplier = 1.0  # Normal time + medium quality = base
                else:
                    time_multiplier = 0.8  # Slow + medium quality = penalty
            else:
                # For poor answers, time doesn't help much
                time_multiplier = 1.0
        else:
            time_multiplier = 1.0
        
        # Severity weight
        severity_weights = {
            "P0": 1.5,  # Critical incidents worth more
            "P1": 1.2,  # High severity
            "P2": 1.0,  # Medium severity
            "P3": 0.8   # Low severity
        }
        severity_multiplier = severity_weights.get(severity, 1.0)
        
        # Calculate final rating change
        final_rating_change = int(base_rating_change * time_multiplier * severity_multiplier)
        
        return {
            "base_rating_change": base_rating_change,
            "time_multiplier": time_multiplier,
            "severity_multiplier": severity_multiplier,
            "final_rating_change": final_rating_change,
            "llm_score": llm_score,
            "time_ratio": time_spent_minutes / time_limit_minutes if time_limit_minutes > 0 else 1.0,
            "calculation_breakdown": {
                "severity": severity,
                "time_limit": time_limit_minutes,
                "actual_time": time_spent_minutes,
                "llm_score": llm_score,
                "quality_category": "high" if llm_score >= 80 else "medium" if llm_score >= 50 else "poor"
            }
        }
    
    @classmethod
    def calculate_incident_rating(
        cls,
        time_limit_minutes: int,
        actual_time_minutes: int,
        solution_type: str,
        severity: str,
        was_successful: bool = True,
        was_escalated: bool = False,
        was_abandoned: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate rating change for a single incident resolution (backward compatibility)
        """
        return cls.calculate_incident_rating_with_llm(
            time_limit_minutes=time_limit_minutes,
            actual_time_minutes=actual_time_minutes,
            solution_type=solution_type,
            severity=severity,
            was_successful=was_successful,
            was_escalated=was_escalated,
            was_abandoned=was_abandoned,
            llm_score=None,
            llm_is_correct=None
        )
    
    @classmethod
    def _calculate_penalty_rating(cls, penalty_type: str) -> Dict[str, Any]:
        """Calculate rating for penalty scenarios"""
        penalty_points = cls.PENALTIES.get(penalty_type, 0)
        
        return {
            "base_points": 0,
            "speed_bonus": 0,
            "quality_multiplier": 1.0,
            "total_points": penalty_points,
            "time_ratio": 1.0,
            "penalty_type": penalty_type,
            "calculation_breakdown": {
                "penalty_applied": penalty_type,
                "penalty_points": penalty_points
            }
        }
    
    @classmethod
    def _get_speed_bonus(cls, time_ratio: float) -> int:
        """Get speed bonus based on time ratio"""
        for category, (min_ratio, max_ratio, bonus) in cls.SPEED_BONUSES.items():
            if min_ratio <= time_ratio < max_ratio:
                return bonus
        return 0
    
    @classmethod
    def _get_speed_category(cls, time_ratio: float) -> str:
        """Get speed category description"""
        for category, (min_ratio, max_ratio, _) in cls.SPEED_BONUSES.items():
            if min_ratio <= time_ratio < max_ratio:
                return category
        return "poor"
    
    @classmethod
    def update_user_rating(
        cls,
        current_rating: int,
        incident_results: list,
        total_incidents: int = None
    ) -> Dict[str, Any]:
        """
        Update user's overall rating based on multiple incidents
        
        Args:
            current_rating: Current user rating
            incident_results: List of incident rating results
            total_incidents: Total number of incidents in session
            
        Returns:
            Dict containing updated rating and statistics
        """
        
        if not incident_results:
            return {
                "new_rating": current_rating,
                "rating_change": 0,
                "session_performance": {}
            }
        
        # Calculate total points from all incidents
        total_points = sum(result.get("total_points", 0) for result in incident_results)
        
        # Calculate performance metrics
        successful_incidents = len([r for r in incident_results if r.get("total_points", 0) > 0])
        total_attempts = len(incident_results)
        success_rate = (successful_incidents / total_attempts) if total_attempts > 0 else 0
        
        # Calculate average resolution time
        resolution_times = []
        for result in incident_results:
            breakdown = result.get("calculation_breakdown", {})
            if "actual_time" in breakdown and "time_limit" in breakdown:
                resolution_times.append(breakdown["actual_time"])
        
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        
        # Apply rating change with some smoothing to prevent wild swings
        rating_change = cls._apply_rating_smoothing(total_points, current_rating)
        new_rating = max(800, min(1600, current_rating + rating_change))
        
        # Calculate skill-specific ratings (simplified for now)
        skill_ratings = cls._calculate_skill_ratings(incident_results)
        
        return {
            "new_rating": new_rating,
            "rating_change": rating_change,
            "total_points_earned": total_points,
            "success_rate": success_rate,
            "average_resolution_time": avg_resolution_time,
            "skill_ratings": skill_ratings,
            "session_performance": {
                "total_incidents": total_attempts,
                "successful_incidents": successful_incidents,
                "failed_incidents": total_attempts - successful_incidents,
                "incident_results": incident_results
            }
        }
    
    @classmethod
    def _apply_rating_smoothing(cls, points_change: int, current_rating: int) -> int:
        """
        Apply smoothing to prevent wild rating swings
        Higher rated users need more points to increase rating
        """
        
        # Base smoothing factor
        smoothing_factor = 1.0
        
        # Adjust smoothing based on current rating
        if current_rating >= 1400:  # Staff level - harder to improve
            smoothing_factor = 0.5
        elif current_rating >= 1200:  # Senior level
            smoothing_factor = 0.7
        elif current_rating >= 1000:  # Mid level
            smoothing_factor = 0.8
        # Junior level (800-999) uses full smoothing factor
        
        # Apply smoothing
        smoothed_change = points_change * smoothing_factor
        
        return round(smoothed_change)
    
    @classmethod
    def _calculate_skill_ratings(cls, incident_results: list) -> Dict[str, int]:
        """
        Calculate skill-specific ratings based on incident performance
        This is a simplified version - could be enhanced with more sophisticated analysis
        """
        
        if not incident_results:
            return {
                "debugging_skill": 800,
                "system_design": 800,
                "incident_response": 800,
                "communication": 800
            }
        
        # Analyze incident patterns to determine skill ratings
        successful_incidents = [r for r in incident_results if r.get("total_points", 0) > 0]
        success_rate = len(successful_incidents) / len(incident_results) if incident_results else 0
        
        # Base skill ratings on overall performance with some variation
        base_skill = 800 + (success_rate * 600)  # Scale 800-1400 based on success rate
        
        return {
            "debugging_skill": round(base_skill + (success_rate * 50)),
            "system_design": round(base_skill + (success_rate * 30)),
            "incident_response": round(base_skill + (success_rate * 80)),
            "communication": round(base_skill + (success_rate * 20))
        }
    
    @classmethod
    def get_rating_category(cls, rating: int) -> str:
        """Get rating category name based on numeric rating"""
        for category, (min_rating, max_rating) in cls.RATING_CATEGORIES.items():
            if min_rating <= rating <= max_rating:
                return category
        return "junior"
    
    @classmethod
    def get_rating_percentile(cls, rating: int) -> float:
        """Estimate rating percentile (0-100)"""
        # Rough percentile estimation based on rating distribution
        if rating >= 1500:
            return 95.0
        elif rating >= 1400:
            return 85.0
        elif rating >= 1300:
            return 70.0
        elif rating >= 1200:
            return 50.0
        elif rating >= 1100:
            return 30.0
        elif rating >= 1000:
            return 15.0
        elif rating >= 900:
            return 5.0
        else:
            return 1.0
    
    @classmethod
    def generate_rating_report(cls, user_rating: int, recent_incidents: list = None) -> Dict[str, Any]:
        """
        Generate a comprehensive rating report for a user
        """
        
        category = cls.get_rating_category(user_rating)
        percentile = cls.get_rating_percentile(user_rating)
        
        report = {
            "current_rating": user_rating,
            "category": category,
            "percentile": percentile,
            "rating_range": cls.RATING_CATEGORIES[category],
            "next_category_threshold": cls._get_next_threshold(user_rating),
            "points_to_next_category": cls._get_points_to_next_category(user_rating),
            "recent_performance": cls._analyze_recent_performance(recent_incidents) if recent_incidents else None
        }
        
        return report
    
    @classmethod
    def _get_next_threshold(cls, rating: int) -> int:
        """Get the rating threshold for the next category"""
        for category, (min_rating, max_rating) in cls.RATING_CATEGORIES.items():
            if rating < max_rating:
                return max_rating
        return 1600
    
    @classmethod
    def _get_points_to_next_category(cls, rating: int) -> int:
        """Calculate points needed to reach next category"""
        next_threshold = cls._get_next_threshold(rating)
        return max(0, next_threshold - rating)
    
    @classmethod
    def _analyze_recent_performance(cls, recent_incidents: list) -> Dict[str, Any]:
        """Analyze recent incident performance patterns"""
        if not recent_incidents:
            return None
        
        total_incidents = len(recent_incidents)
        successful = len([i for i in recent_incidents if i.get("total_points", 0) > 0])
        
        # Calculate trend (simplified)
        if total_incidents >= 3:
            recent_3 = recent_incidents[:3]
            older_3 = recent_incidents[3:6] if len(recent_incidents) >= 6 else recent_incidents[3:]
            
            recent_success_rate = len([i for i in recent_3 if i.get("total_points", 0) > 0]) / len(recent_3)
            older_success_rate = len([i for i in older_3 if i.get("total_points", 0) > 0]) / len(older_3) if older_3 else 0
            
            if recent_success_rate > older_success_rate:
                trend = "improving"
            elif recent_success_rate < older_success_rate:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "total_incidents": total_incidents,
            "success_rate": successful / total_incidents if total_incidents > 0 else 0,
            "trend": trend,
            "average_points_per_incident": sum(i.get("total_points", 0) for i in recent_incidents) / total_incidents if total_incidents > 0 else 0
        }
