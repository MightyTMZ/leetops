from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Avg, Count
from datetime import datetime, timedelta
import json

from .models import (
    Company, Incident, UserRating, SimulationSession, 
    IncidentAttempt, Rating
)
from .incident_generator import IncidentGenerator, create_company_data
from .rating_calculator import RatingCalculator
from users.models import User


class CompanyListView(generics.ListAPIView):
    """List all available companies for simulation"""
    queryset = Company.objects.all()
    serializer_class = None  # Will be implemented with DRF serializers
    
    def get(self, request):
        companies = Company.objects.all()
        companies_data = []
        
        for company in companies:
            companies_data.append({
                'id': company.id,
                'name': company.name,
                'slug': company.slug,
                'description': company.description,
                'industry': company.industry,
                'company_size': company.company_size,
                'tech_stack': company.tech_stack,
                'focus_areas': company.focus_areas,
                'incident_frequency': company.incident_frequency,
                'severity_distribution': company.severity_distribution
            })
        
        return Response({
            'companies': companies_data,
            'total': len(companies_data)
        })


class CompanyDetailView(APIView):
    """Get detailed information about a specific company"""
    
    def get(self, request, company_id):
        company = get_object_or_404(Company, id=company_id)
        
        # Get company statistics
        total_sessions = SimulationSession.objects.filter(company=company).count()
        avg_rating = UserRating.objects.filter(
            user__simulationsession__company=company
        ).aggregate(avg_rating=Avg('overall_rating'))['avg_rating'] or 800
        
        company_data = {
            'id': company.id,
            'name': company.name,
            'slug': company.slug,
            'description': company.description,
            'industry': company.industry,
            'company_size': company.company_size,
            'tech_stack': company.tech_stack,
            'focus_areas': company.focus_areas,
            'incident_frequency': company.incident_frequency,
            'severity_distribution': company.severity_distribution,
            'work_hours_start': company.work_hours_start,
            'work_hours_end': company.work_hours_end,
            'statistics': {
                'total_simulation_sessions': total_sessions,
                'average_rating': round(avg_rating, 1)
            }
        }
        
        return Response(company_data)


class StartSimulationView(APIView):
    """Start a new simulation session for a user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        company_id = request.data.get('company_id')
        scheduled_duration_hours = request.data.get('duration_hours', 8)
        
        if not company_id:
            return Response(
                {'error': 'company_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        company = get_object_or_404(Company, id=company_id)
        
        # Check if user has an active session
        active_session = SimulationSession.objects.filter(
            user=request.user, 
            is_active=True
        ).first()
        
        if active_session:
            return Response(
                {'error': 'User already has an active simulation session'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new simulation session
        session = SimulationSession.objects.create(
            user=request.user,
            company=company,
            scheduled_duration_hours=scheduled_duration_hours
        )
        
        # Generate incident schedule for the session
        generator = IncidentGenerator(company.name)
        incident_schedule = generator.generate_incident_schedule(
            work_hours=(company.work_hours_start.hour, company.work_hours_end.hour),
            num_incidents=None  # Use default based on company frequency
        )
        
        session_data = {
            'session_id': str(session.id),
            'company': {
                'id': company.id,
                'name': company.name,
                'slug': company.slug
            },
            'scheduled_duration_hours': session.scheduled_duration_hours,
            'started_at': session.started_at,
            'incident_schedule': incident_schedule,
            'total_incidents_planned': len(incident_schedule)
        }
        
        return Response(session_data, status=status.HTTP_201_CREATED)


class GenerateIncidentView(APIView):
    """Generate a new incident for an active simulation session"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        session_id = request.data.get('session_id')
        severity = request.data.get('severity')  # Optional
        time_of_day = request.data.get('time_of_day')  # Optional
        
        if not session_id:
            return Response(
                {'error': 'session_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session = get_object_or_404(SimulationSession, id=session_id, user=request.user)
        
        if not session.is_active:
            return Response(
                {'error': 'Simulation session is not active'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate incident
        generator = IncidentGenerator(session.company.name)
        incident_data = generator.generate_incident(severity=severity, time_of_day=time_of_day)
        
        # Create incident in database
        incident = Incident.objects.create(
            company=session.company,
            title=incident_data['title'],
            description=incident_data['description'],
            severity=incident_data['severity'],
            time_limit_minutes=incident_data['time_limit'],
            affected_services=incident_data['affected_services'],
            error_logs=incident_data['error_logs'],
            codebase_context=incident_data['codebase_context'],
            monitoring_dashboard_url=incident_data['monitoring_dashboard_url'],
            assigned_user=request.user
        )
        
        # Update session incident count
        session.incident_count += 1
        session.save()
        
        incident_response = {
            'incident_id': str(incident.id),
            'title': incident.title,
            'description': incident.description,
            'severity': incident.severity,
            'time_limit_minutes': incident.time_limit_minutes,
            'affected_services': incident.affected_services,
            'error_logs': incident.error_logs,
            'codebase_context': incident.codebase_context,
            'monitoring_dashboard_url': incident.monitoring_dashboard_url,
            'started_at': incident.started_at,
            'status': incident.status
        }
        
        return Response(incident_response, status=status.HTTP_201_CREATED)


class UserRatingView(APIView):
    """Get user's current rating and performance statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user_rating, created = UserRating.objects.get_or_create(user=request.user)
        
        # Get recent incidents for performance analysis
        recent_attempts = IncidentAttempt.objects.filter(user=request.user)[:20]
        recent_results = []
        for attempt in recent_attempts:
            recent_results.append({
                'total_points': attempt.points_earned,
                'calculation_breakdown': {
                    'severity': attempt.incident.severity,
                    'time_limit': attempt.incident.time_limit_minutes,
                    'actual_time': attempt.time_spent_minutes,
                    'solution_type': 'root_cause' if attempt.was_root_cause_fix else 'workaround'
                }
            })
        
        # Generate rating report
        rating_report = RatingCalculator.generate_rating_report(
            user_rating.overall_rating, 
            recent_results
        )
        
        response_data = {
            'user_id': request.user.id,
            'email': request.user.email,
            'overall_rating': user_rating.overall_rating,
            'rating_category': rating_report['category'],
            'rating_percentile': rating_report['percentile'],
            'rating_range': rating_report['rating_range'],
            'points_to_next_category': rating_report['points_to_next_category'],
            'skill_ratings': {
                'debugging_skill': user_rating.debugging_skill,
                'system_design': user_rating.system_design,
                'incident_response': user_rating.incident_response,
                'communication': user_rating.communication
            },
            'statistics': {
                'total_incidents_resolved': user_rating.total_incidents_resolved,
                'average_resolution_time': user_rating.average_resolution_time,
                'success_rate': user_rating.success_rate
            },
            'recent_performance': rating_report['recent_performance']
        }
        
        return Response(response_data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def end_simulation(request):
    """End an active simulation session"""
    session_id = request.data.get('session_id')
    
    if not session_id:
        return Response(
            {'error': 'session_id is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    session = get_object_or_404(SimulationSession, id=session_id, user=request.user)
    
    if not session.is_active:
        return Response(
            {'error': 'Session is not active'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # End the session
    session.is_active = False
    session.is_completed = True
    session.ended_at = timezone.now()
    session.save()
    
    return Response({
        'session_ended': True,
        'session_id': str(session.id),
        'ended_at': session.ended_at,
        'total_duration_hours': (session.ended_at - session.started_at).total_seconds() / 3600
    })


class ResolveIncidentView(APIView):
    """Resolve an incident and calculate rating"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        incident_id = request.data.get('incident_id')
        session_id = request.data.get('session_id')
        resolution_approach = request.data.get('resolution_approach', '')
        code_changes = request.data.get('code_changes', '')
        commands_executed = request.data.get('commands_executed', [])
        solution_type = request.data.get('solution_type', 'workaround')
        was_successful = request.data.get('was_successful', True)
        
        if not incident_id or not session_id:
            return Response(
                {'error': 'incident_id and session_id are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        incident = get_object_or_404(Incident, id=incident_id, assigned_user=request.user)
        session = get_object_or_404(SimulationSession, id=session_id, user=request.user)
        
        if incident.status != 'active':
            return Response(
                {'error': 'Incident is not active'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate time spent
        time_spent = timezone.now() - incident.started_at
        time_spent_minutes = int(time_spent.total_seconds() / 60)
        
        # Determine if it was escalated or abandoned
        was_escalated = solution_type == 'escalation'
        was_abandoned = solution_type == 'abandonment'
        
        # Calculate rating
        rating_result = RatingCalculator.calculate_incident_rating(
            time_limit_minutes=incident.time_limit_minutes,
            actual_time_minutes=time_spent_minutes,
            solution_type=solution_type,
            severity=incident.severity,
            was_successful=was_successful,
            was_escalated=was_escalated,
            was_abandoned=was_abandoned
        )
        
        # Create incident attempt record
        attempt = IncidentAttempt.objects.create(
            incident=incident,
            user=request.user,
            session=session,
            time_spent_minutes=time_spent_minutes,
            resolution_approach=resolution_approach,
            code_changes=code_changes,
            commands_executed=commands_executed,
            was_successful=was_successful,
            was_root_cause_fix=(solution_type == 'root_cause'),
            points_earned=rating_result['total_points'],
            quality_score=rating_result.get('quality_multiplier', 1.0)
        )
        
        # Update incident status
        incident.status = 'resolved' if was_successful else 'escalated' if was_escalated else 'abandoned'
        incident.resolved_at = timezone.now()
        incident.resolution_notes = resolution_approach
        incident.solution_type = solution_type
        incident.save()
        
        # Update session statistics
        if was_successful:
            session.incidents_resolved += 1
        elif was_escalated:
            session.incidents_escalated += 1
        elif was_abandoned:
            session.incidents_abandoned += 1
        
        session.total_time_spent_minutes += time_spent_minutes
        session.save()
        
        # Update user rating
        user_rating, created = UserRating.objects.get_or_create(user=request.user)
        
        # Get recent incident results for rating calculation
        recent_attempts = IncidentAttempt.objects.filter(user=request.user)[:10]
        recent_results = []
        for attempt in recent_attempts:
            recent_results.append({
                'total_points': attempt.points_earned,
                'calculation_breakdown': {
                    'severity': attempt.incident.severity,
                    'time_limit': attempt.incident.time_limit_minutes,
                    'actual_time': attempt.time_spent_minutes,
                    'solution_type': 'root_cause' if attempt.was_root_cause_fix else 'workaround'
                }
            })
        
        rating_update = RatingCalculator.update_user_rating(
            current_rating=user_rating.overall_rating,
            incident_results=recent_results
        )
        
        # Update user rating record
        user_rating.overall_rating = rating_update['new_rating']
        user_rating.total_incidents_resolved += 1 if was_successful else 0
        user_rating.average_resolution_time = rating_update['average_resolution_time']
        user_rating.success_rate = rating_update['success_rate']
        
        # Update skill ratings
        skill_ratings = rating_update['skill_ratings']
        user_rating.debugging_skill = skill_ratings['debugging_skill']
        user_rating.system_design = skill_ratings['system_design']
        user_rating.incident_response = skill_ratings['incident_response']
        user_rating.communication = skill_ratings['communication']
        
        user_rating.save()
        
        response_data = {
            'incident_resolved': True,
            'time_spent_minutes': time_spent_minutes,
            'rating_result': rating_result,
            'rating_change': rating_update['rating_change'],
            'new_overall_rating': rating_update['new_rating'],
            'attempt_id': attempt.id,
            'incident_status': incident.status
        }
        
        return Response(response_data)


@api_view(['POST'])
def initialize_companies(request):
    """Initialize company data (admin endpoint)"""
    companies_data = create_company_data()
    
    created_companies = []
    for company_data in companies_data:
        company, created = Company.objects.get_or_create(
            slug=company_data['slug'],
            defaults=company_data
        )
        if created:
            created_companies.append(company.name)
    
    return Response({
        'companies_created': created_companies,
        'total_companies': Company.objects.count()
    })
