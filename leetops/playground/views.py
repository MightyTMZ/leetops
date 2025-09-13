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
            incident = get_object_or_404(Incident, id=incident_id, assigned_user=request.user)
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
        
        # Perform LLM grading
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
            
            # Override was_successful based on LLM grading if it's more accurate
            llm_is_correct = llm_grading_result.get('is_correct', was_successful)
            if not was_abandoned and not was_escalated:
                was_successful = llm_is_correct
            
        except Exception as e:
            print(f"LLM grading failed: {e}")
            # Fallback to basic grading
            llm_grading_result = {
                'overall_score': 5,
                'technical_accuracy': 5,
                'problem_solving': 5,
                'communication': 5,
                'efficiency': 5,
                'best_practices': 5,
                'is_correct': was_successful,
                'feedback': {
                    'strengths': ['Attempted to resolve the incident'],
                    'weaknesses': ['Could improve technical approach'],
                    'suggestions': ['Review incident response best practices'],
                    'overall_feedback': 'Grading completed using fallback system due to LLM unavailability.'
                },
                'correctness_explanation': 'Solution evaluated using fallback system',
                'improvement_areas': ['Technical accuracy', 'Problem-solving approach'],
                'grading_method': 'fallback'
            }
        
        # Calculate rating with LLM-informed scoring
        rating_result = RatingCalculator.calculate_incident_rating_with_llm(
            time_limit_minutes=incident.time_limit_minutes,
            actual_time_minutes=time_spent_minutes,
            solution_type=solution_type,
            severity=incident.severity,
            was_successful=was_successful,
            was_escalated=was_escalated,
            was_abandoned=was_abandoned,
            llm_score=llm_grading_result.get('overall_score'),
            llm_is_correct=llm_grading_result.get('is_correct')
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
                points_earned=rating_result['total_points'],
                quality_score=rating_result.get('quality_multiplier', 1.0),
                # LLM grading results
                llm_grade=llm_grading_result.get('overall_score'),
                llm_technical_accuracy=llm_grading_result.get('technical_accuracy'),
                llm_problem_solving=llm_grading_result.get('problem_solving'),
                llm_communication=llm_grading_result.get('communication'),
                llm_efficiency=llm_grading_result.get('efficiency'),
                llm_best_practices=llm_grading_result.get('best_practices'),
                llm_is_correct=llm_grading_result.get('is_correct'),
                llm_feedback=llm_grading_result.get('feedback', {}),
                llm_correctness_explanation=llm_grading_result.get('correctness_explanation', ''),
                llm_improvement_areas=llm_grading_result.get('improvement_areas', []),
                llm_grading_method=llm_grading_result.get('grading_method', 'llm')
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
        
        # Get recent incident results for rating calculation
        recent_attempts = IncidentAttempt.objects.filter(user=request.user)[:10]
        recent_results = []
        for attempt_obj in recent_attempts:
            recent_results.append({
                'total_points': attempt_obj.points_earned,
                'calculation_breakdown': {
                    'severity': attempt_obj.incident.severity,
                    'time_limit': attempt_obj.incident.time_limit_minutes,
                    'actual_time': attempt_obj.time_spent_minutes,
                    'solution_type': 'root_cause' if attempt_obj.was_root_cause_fix else 'workaround'
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
            'incident_status': incident.status,
            'llm_grading': {
                'overall_score': llm_grading_result.get('overall_score'),
                'technical_accuracy': llm_grading_result.get('technical_accuracy'),
                'problem_solving': llm_grading_result.get('problem_solving'),
                'communication': llm_grading_result.get('communication'),
                'efficiency': llm_grading_result.get('efficiency'),
                'best_practices': llm_grading_result.get('best_practices'),
                'is_correct': llm_grading_result.get('is_correct'),
                'feedback': llm_grading_result.get('feedback', {}),
                'correctness_explanation': llm_grading_result.get('correctness_explanation', ''),
                'improvement_areas': llm_grading_result.get('improvement_areas', []),
                'grading_method': llm_grading_result.get('grading_method', 'llm')
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
