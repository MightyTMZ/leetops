from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Company(models.Model):
    """Companies that users can select for simulation"""
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    avatar = models.ImageField(upload_to="company_avatars/", blank=True, null=True)
    industry = models.CharField(max_length=100)
    company_size = models.CharField(max_length=50)  # Startup, Mid-size, Large, Enterprise
    tech_stack = models.JSONField(default=list)  # List of technologies
    focus_areas = models.JSONField(default=list)  # e.g., ["distributed-systems", "ml", "security"]
    
    # Company-specific settings
    incident_frequency = models.FloatField(default=0.1)  # Incidents per hour
    severity_distribution = models.JSONField(default=dict)  # P0: 0.1, P1: 0.3, P2: 0.6
    work_hours_start = models.TimeField(default="09:00")
    work_hours_end = models.TimeField(default="17:00")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Incident(models.Model):
    """Individual incidents that occur during simulation"""
    SEVERITY_CHOICES = [
        ('P0', 'Critical - Service Down'),
        ('P1', 'High - Major Impact'),
        ('P2', 'Medium - Minor Impact'),
        ('P3', 'Low - Cosmetic Issue'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated'),
        ('abandoned', 'Abandoned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=2, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Technical details
    affected_services = models.JSONField(default=list)
    error_logs = models.TextField(blank=True)
    monitoring_dashboard_url = models.URLField(blank=True)
    codebase_context = models.TextField(blank=True)
    
    # Timing
    time_limit_minutes = models.PositiveIntegerField()  # Time allowed to resolve
    started_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Resolution tracking
    assigned_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    solution_type = models.CharField(max_length=50, blank=True)  # root-cause, workaround, escalation
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.title} ({self.severity}) - {self.company.name}"


class UserRating(models.Model):
    """Enhanced user rating system"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Overall rating (800-1600 scale)
    overall_rating = models.PositiveIntegerField(default=800)
    
    # Skill-specific ratings
    debugging_skill = models.PositiveIntegerField(default=800)
    system_design = models.PositiveIntegerField(default=800)
    incident_response = models.PositiveIntegerField(default=800)
    communication = models.PositiveIntegerField(default=800)
    
    # Statistics
    total_incidents_resolved = models.PositiveIntegerField(default=0)
    average_resolution_time = models.FloatField(default=0.0)  # in minutes
    success_rate = models.FloatField(default=0.0)  # percentage
    
    # Company-specific ratings
    company_ratings = models.JSONField(default=dict)  # {company_id: rating}
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Rating"
        verbose_name_plural = "User Ratings"
    
    def __str__(self):
        return f"{self.user.email} - Rating: {self.overall_rating}"


class SimulationSession(models.Model):
    """A complete simulation session for a user"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    # Session timing
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    scheduled_duration_hours = models.PositiveIntegerField(default=8)  # 8-hour work day
    
    # Session configuration
    incident_count = models.PositiveIntegerField(default=0)
    incidents_resolved = models.PositiveIntegerField(default=0)
    incidents_escalated = models.PositiveIntegerField(default=0)
    incidents_abandoned = models.PositiveIntegerField(default=0)
    
    # Performance metrics
    total_time_spent_minutes = models.PositiveIntegerField(default=0)
    average_resolution_time = models.FloatField(default=0.0)
    rating_change = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.company.name} ({self.started_at.date()})"


class IncidentAttempt(models.Model):
    """User's attempt to resolve a specific incident"""
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.ForeignKey(SimulationSession, on_delete=models.CASCADE)
    
    # Attempt timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_minutes = models.PositiveIntegerField(default=0)
    
    # Resolution details
    resolution_approach = models.TextField(blank=True)
    code_changes = models.TextField(blank=True)  # JSON of file changes
    commands_executed = models.JSONField(default=list)
    resources_accessed = models.JSONField(default=list)
    
    # Outcome
    was_successful = models.BooleanField(default=False)
    was_root_cause_fix = models.BooleanField(default=False)
    points_earned = models.IntegerField(default=0)
    quality_score = models.FloatField(default=0.0)  # 0.0 to 1.0
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        status = "Success" if self.was_successful else "Failed"
        return f"{self.user.email} - {self.incident.title} ({status})"


# Legacy models for backward compatibility
class Rating(models.Model):
    """Legacy rating model - keeping for compatibility"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=100)
    
    def __str__(self):
        return f"{self.user.email} - {self.rating}"


class Simulation(models.Model):
    """Legacy simulation model - keeping for compatibility"""
    company = models.CharField(max_length=255)
    company_avatar = models.ImageField(upload_to="company_avatars/", blank=True, null=True)
    details = models.TextField()
    
    def __str__(self):
        return self.company


class CompletedSimulation(models.Model):
    """Legacy completed simulation model - keeping for compatibility"""
    simulation = models.ForeignKey(Simulation, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plus_minus = models.IntegerField()  # in rating
    summary = models.TextField()
    time_spent = models.IntegerField(default=1200)  # in seconds
    
    def __str__(self):
        return f"{self.user.email} - {self.simulation.company}"
