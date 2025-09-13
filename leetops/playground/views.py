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
from .llm_grading import llm_grader
from users.models import User


class CompanyListView(generics.ListAPIView):
    """List all available companies for simulation"""
    queryset = Company.objects.all()
    serializer_class = None  # Will be implemented with DRF serializers
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        companies = Company.objects.all()
        companies_data = []
        
        for company in companies:
            companies_data.append({
                'id': company.id,
                'name': company.name,
                'slug': company.slug,
                'description': company.description,
                'avatar': company.avatar.url if company.avatar else None,
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
    permission_classes = [permissions.IsAuthenticated]
    
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


class CompanyIncidentsView(APIView):
    """Get incidents for a specific company"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, company_id):
        company = get_object_or_404(Company, id=company_id)
        
        # Get active incidents for this company
        incidents = Incident.objects.filter(
            company=company,
            status='active'
        ).order_by('-started_at')
        
        incidents_data = []
        for incident in incidents:
            incidents_data.append({
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
            })
        
        return Response({
            'incidents': incidents_data,
            'total': len(incidents_data),
            'company_id': company_id,
            'company_name': company.name
        })


class GenerateIncidentView(APIView):
    """Generate a new incident for a company"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        company_id = request.data.get('company_id')
        severity = request.data.get('severity')  # Optional
        time_of_day = request.data.get('time_of_day')  # Optional
        
        if not company_id:
            return Response(
                {'error': 'company_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        company = get_object_or_404(Company, id=company_id)
        
        # Generate incident
        generator = IncidentGenerator(company.name)
        incident_data = generator.generate_incident(severity=severity, time_of_day=time_of_day)
        
        # Create incident in database
        incident = Incident.objects.create(
            company=company,
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


class ResolveIncidentView(APIView):
    """Resolve an incident and calculate rating with LLM grading"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        print(f"DEBUG: ResolveIncident request data: {request.data}")
        print(f"DEBUG: Request user: {request.user}")
        
        incident_id = request.data.get('incident_id') or request.data.get('incidentId')
        resolution_approach = request.data.get('resolution_approach') or request.data.get('resolutionApproach', '')
        code_changes = request.data.get('code_changes') or request.data.get('codeChanges', '')
        commands_executed = request.data.get('commands_executed') or request.data.get('commandsExecuted', [])
        solution_type = request.data.get('solution_type') or request.data.get('solutionType', 'workaround')
        was_successful = request.data.get('was_successful') or request.data.get('wasSuccessful', True)
        
        print(f"DEBUG: Parsed incident_id: {incident_id}")
        print(f"DEBUG: Parsed solution_type: {solution_type}")
        print(f"DEBUG: Parsed was_successful: {was_successful}")
        
        if not incident_id:
            print("DEBUG: ERROR - incident_id is missing!")
            return Response(
                {'error': 'incident_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f"DEBUG: Looking up incident with id: {incident_id}")
        try:
            incident = get_object_or_404(Incident, id=incident_id)
            print(f"DEBUG: Found incident: {incident.title}")
        except Exception as e:
            print(f"DEBUG: ERROR finding incident: {e}")
            return Response(
                {'error': f'Incident not found: {str(e)}'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
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
        
        # Perform LLM grading with Groq
        try:
            incident_context = {
                'affected_services': incident.affected_services,
                'error_logs': incident.error_logs,
                'codebase_context': incident.codebase_context,
                'monitoring_dashboard_url': incident.monitoring_dashboard_url
            }
            
            llm_grading_result = llm_grader.grade_incident_response(
                incident_title=incident.title,
                incident_description=incident.description,
                incident_severity=incident.severity,
                incident_context=incident_context,
                user_resolution_approach=resolution_approach,
                user_code_changes=code_changes,
                user_commands_executed=commands_executed,
                user_solution_type=solution_type,
                time_spent_minutes=time_spent_minutes,
                time_limit_minutes=incident.time_limit_minutes
            )
            
            # Extract score and feedback from Groq response
            groq_score = llm_grading_result.get('score', 50)
            groq_feedback = llm_grading_result.get('feedback', 'No feedback available')
            
        except Exception as e:
            print(f"Groq grading failed: {e}")
            # Fallback grading
            groq_score = 50
            groq_feedback = "Grading completed using fallback system due to LLM unavailability."
        
        # Calculate rating with new Groq-based scoring
        rating_result = RatingCalculator.calculate_rating_with_groq_score(
            llm_score=groq_score,
            time_spent_minutes=time_spent_minutes,
            time_limit_minutes=incident.time_limit_minutes,
            severity=incident.severity
        )
        
        # Create incident attempt record with LLM grading data
        print(f"DEBUG: Creating IncidentAttempt...")
        try:
            attempt = IncidentAttempt.objects.create(
                incident=incident,
                user=request.user,
                session=None,  # No session needed
                time_spent_minutes=time_spent_minutes,
                resolution_approach=resolution_approach,
                code_changes=code_changes,
                commands_executed=commands_executed,
                was_successful=was_successful,
                was_root_cause_fix=(solution_type == 'root_cause'),
                points_earned=rating_result['final_rating_change'],
                quality_score=rating_result.get('time_multiplier', 1.0),
                # Groq grading results
                llm_grade=groq_score,
                llm_technical_accuracy=groq_score,  # Use same score for all fields
                llm_problem_solving=groq_score,
                llm_communication=groq_score,
                llm_efficiency=groq_score,
                llm_best_practices=groq_score,
                llm_is_correct=(groq_score >= 50),
                llm_feedback={'overall_feedback': groq_feedback},
                llm_correctness_explanation=groq_feedback,
                llm_improvement_areas=[],
                llm_grading_method=llm_grading_result.get('grading_method', 'groq')
            )
            print(f"DEBUG: IncidentAttempt created successfully: {attempt.id}")
        except Exception as e:
            print(f"DEBUG: ERROR creating IncidentAttempt: {e}")
            return Response(
                {'error': f'Failed to create incident attempt: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update incident status
        incident.status = 'resolved' if was_successful else 'escalated' if was_escalated else 'abandoned'
        incident.resolved_at = timezone.now()
        incident.resolution_notes = resolution_approach
        incident.solution_type = solution_type
        incident.save()
        
        # Update user rating
        user_rating, created = UserRating.objects.get_or_create(user=request.user)
        
        # Apply the rating change directly
        new_rating = max(800, min(1600, user_rating.overall_rating + rating_result['final_rating_change']))
        rating_change = new_rating - user_rating.overall_rating
        
        # Update user rating record
        user_rating.overall_rating = new_rating
        user_rating.total_incidents_resolved += 1 if groq_score >= 50 else 0
        user_rating.average_resolution_time = time_spent_minutes  # Simple update for now
        user_rating.success_rate = 0.8 if groq_score >= 50 else 0.2  # Simple calculation
        
        # Update skill ratings based on Groq score
        skill_base = 800 + (groq_score * 6)  # Scale 800-1400 based on score
        user_rating.debugging_skill = min(1600, skill_base + 20)
        user_rating.system_design = min(1600, skill_base + 10)
        user_rating.incident_response = min(1600, skill_base + 30)
        user_rating.communication = min(1600, skill_base + 5)
        
        user_rating.save()
        
        response_data = {
            'incident_resolved': True,
            'time_spent_minutes': time_spent_minutes,
            'rating_result': rating_result,
            'rating_change': rating_change,
            'new_overall_rating': new_rating,
            'attempt_id': attempt.id,
            'incident_status': incident.status,
            'groq_grading': {
                'score': groq_score,
                'feedback': groq_feedback,
                'grading_method': llm_grading_result.get('grading_method', 'groq')
            }
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
