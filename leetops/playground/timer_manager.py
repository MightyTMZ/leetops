"""
Timer Management System for LeetOps
Handles time pressure simulation and incident timing
"""

import time
from datetime import datetime, timedelta
from django.utils import timezone
from typing import Dict, Any, Optional
import threading


class TimerManager:
    """
    Manages timers for incident resolution with real-time updates
    """
    
    def __init__(self):
        self.active_timers = {}  # {incident_id: timer_info}
        self.timer_callbacks = {}  # {incident_id: callback_function}
    
    def start_timer(self, incident_id: str, time_limit_minutes: int, callback=None) -> Dict[str, Any]:
        """
        Start a timer for an incident
        
        Args:
            incident_id: Unique identifier for the incident
            time_limit_minutes: Time limit in minutes
            callback: Optional callback function when timer expires
            
        Returns:
            Timer information including start time and end time
        """
        
        start_time = timezone.now()
        end_time = start_time + timedelta(minutes=time_limit_minutes)
        
        timer_info = {
            'incident_id': incident_id,
            'start_time': start_time,
            'end_time': end_time,
            'time_limit_minutes': time_limit_minutes,
            'is_active': True,
            'remaining_seconds': time_limit_minutes * 60,
            'elapsed_seconds': 0
        }
        
        self.active_timers[incident_id] = timer_info
        
        if callback:
            self.timer_callbacks[incident_id] = callback
        
        # Start background timer thread
        timer_thread = threading.Thread(
            target=self._timer_thread,
            args=(incident_id, time_limit_minutes * 60)
        )
        timer_thread.daemon = True
        timer_thread.start()
        
        return timer_info
    
    def stop_timer(self, incident_id: str) -> Dict[str, Any]:
        """
        Stop a timer and return final timing information
        
        Args:
            incident_id: Unique identifier for the incident
            
        Returns:
            Final timer information
        """
        
        if incident_id not in self.active_timers:
            return None
        
        timer_info = self.active_timers[incident_id]
        timer_info['is_active'] = False
        timer_info['stopped_time'] = timezone.now()
        
        # Calculate final elapsed time
        elapsed = timer_info['stopped_time'] - timer_info['start_time']
        timer_info['elapsed_seconds'] = int(elapsed.total_seconds())
        timer_info['remaining_seconds'] = max(0, timer_info['remaining_seconds'] - timer_info['elapsed_seconds'])
        
        # Remove from active timers
        del self.active_timers[incident_id]
        
        if incident_id in self.timer_callbacks:
            del self.timer_callbacks[incident_id]
        
        return timer_info
    
    def get_timer_status(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current timer status for an incident
        
        Args:
            incident_id: Unique identifier for the incident
            
        Returns:
            Current timer status or None if not found
        """
        
        if incident_id not in self.active_timers:
            return None
        
        timer_info = self.active_timers[incident_id]
        current_time = timezone.now()
        
        # Update elapsed time
        elapsed = current_time - timer_info['start_time']
        timer_info['elapsed_seconds'] = int(elapsed.total_seconds())
        timer_info['remaining_seconds'] = max(0, timer_info['time_limit_minutes'] * 60 - timer_info['elapsed_seconds'])
        
        # Check if timer has expired
        if current_time >= timer_info['end_time']:
            timer_info['is_expired'] = True
            timer_info['is_active'] = False
            
            # Trigger callback if exists
            if incident_id in self.timer_callbacks:
                callback = self.timer_callbacks[incident_id]
                callback(incident_id, timer_info)
        else:
            timer_info['is_expired'] = False
        
        return timer_info
    
    def _timer_thread(self, incident_id: str, total_seconds: int):
        """
        Background thread that monitors timer expiration
        
        Args:
            incident_id: Unique identifier for the incident
            total_seconds: Total time limit in seconds
        """
        
        time.sleep(total_seconds)
        
        # Check if timer is still active (not manually stopped)
        if incident_id in self.active_timers and self.active_timers[incident_id]['is_active']:
            # Timer expired
            timer_info = self.active_timers[incident_id]
            timer_info['is_expired'] = True
            timer_info['is_active'] = False
            
            # Trigger callback if exists
            if incident_id in self.timer_callbacks:
                callback = self.timer_callbacks[incident_id]
                callback(incident_id, timer_info)
    
    def get_all_active_timers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all active timers
        
        Returns:
            Dictionary of all active timers and their status
        """
        
        active_timers = {}
        for incident_id in list(self.active_timers.keys()):
            status = self.get_timer_status(incident_id)
            if status and status['is_active']:
                active_timers[incident_id] = status
        
        return active_timers
    
    def cleanup_expired_timers(self):
        """Clean up expired timers from memory"""
        
        expired_timers = []
        for incident_id, timer_info in self.active_timers.items():
            if not timer_info['is_active'] or timer_info.get('is_expired', False):
                expired_timers.append(incident_id)
        
        for incident_id in expired_timers:
            if incident_id in self.active_timers:
                del self.active_timers[incident_id]
            if incident_id in self.timer_callbacks:
                del self.timer_callbacks[incident_id]


class IncidentTimer:
    """
    Individual incident timer with pressure simulation features
    """
    
    def __init__(self, incident_id: str, time_limit_minutes: int):
        self.incident_id = incident_id
        self.time_limit_minutes = time_limit_minutes
        self.start_time = None
        self.is_active = False
        self.pressure_levels = self._calculate_pressure_levels()
    
    def _calculate_pressure_levels(self) -> Dict[str, Dict[str, Any]]:
        """Calculate pressure levels based on time remaining"""
        
        total_seconds = self.time_limit_minutes * 60
        
        return {
            'low': {
                'remaining_percentage': (100, 75),
                'color': '#4CAF50',  # Green
                'message': 'Plenty of time remaining',
                'urgency': 'low'
            },
            'medium': {
                'remaining_percentage': (75, 50),
                'color': '#FF9800',  # Orange
                'message': 'Time is running out',
                'urgency': 'medium'
            },
            'high': {
                'remaining_percentage': (50, 25),
                'color': '#FF5722',  # Red
                'message': 'Critical time pressure',
                'urgency': 'high'
            },
            'critical': {
                'remaining_percentage': (25, 0),
                'color': '#F44336',  # Dark Red
                'message': 'EMERGENCY - Time almost up!',
                'urgency': 'critical'
            }
        }
    
    def start(self):
        """Start the timer"""
        self.start_time = timezone.now()
        self.is_active = True
    
    def stop(self):
        """Stop the timer"""
        self.is_active = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current timer status with pressure level"""
        
        if not self.is_active or not self.start_time:
            return {
                'is_active': False,
                'remaining_seconds': 0,
                'elapsed_seconds': 0,
                'pressure_level': 'inactive'
            }
        
        current_time = timezone.now()
        elapsed = current_time - self.start_time
        elapsed_seconds = int(elapsed.total_seconds())
        remaining_seconds = max(0, (self.time_limit_minutes * 60) - elapsed_seconds)
        
        # Calculate pressure level
        remaining_percentage = (remaining_seconds / (self.time_limit_minutes * 60)) * 100
        pressure_level = self._get_pressure_level(remaining_percentage)
        
        return {
            'is_active': self.is_active,
            'remaining_seconds': remaining_seconds,
            'elapsed_seconds': elapsed_seconds,
            'remaining_percentage': remaining_percentage,
            'pressure_level': pressure_level,
            'pressure_info': self.pressure_levels.get(pressure_level, {}),
            'time_limit_minutes': self.time_limit_minutes,
            'start_time': self.start_time,
            'is_expired': remaining_seconds == 0 and self.is_active
        }
    
    def _get_pressure_level(self, remaining_percentage: float) -> str:
        """Determine pressure level based on remaining percentage"""
        
        for level, info in self.pressure_levels.items():
            min_pct, max_pct = info['remaining_percentage']
            if min_pct >= remaining_percentage > max_pct:
                return level
        
        # If remaining percentage is 0 or negative
        if remaining_percentage <= 0:
            return 'critical'
        
        # Default to low if above 100% (shouldn't happen)
        return 'low'


# Global timer manager instance
timer_manager = TimerManager()
