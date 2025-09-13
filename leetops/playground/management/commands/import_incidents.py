import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from playground.models import Incident, Company
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Import incidents from JSON file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='output.json',
            help='Path to the JSON file containing incidents'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            default=2,
            help='User ID to assign incidents to'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        user_id = options['user_id']
        
        # Check if file exists
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'File {file_path} does not exist')
            )
            return
        
        # Check if user exists
        try:
            user = User.objects.get(id=user_id)
            self.stdout.write(f'Assigning incidents to user: {user.email}')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with ID {user_id} does not exist')
            )
            return
        
        # Load JSON data
        with open(file_path, 'r') as f:
            incidents_data = json.load(f)
        
        created_count = 0
        skipped_count = 0
        
        for incident_data in incidents_data:
            company_name = incident_data['company']
            
            # Get or create company
            company, created = Company.objects.get_or_create(
                name=company_name,
                defaults={
                    'slug': company_name.lower().replace(' ', '-'),
                    'description': f'Company: {company_name}',
                    'industry': 'Technology',
                    'company_size': 'Large',
                    'tech_stack': [],
                    'focus_areas': [],
                    'incident_frequency': 0.1,
                    'severity_distribution': {'P0': 0.1, 'P1': 0.3, 'P2': 0.6}
                }
            )
            
            if created:
                self.stdout.write(f'Created new company: {company_name}')
            
            # Create incident
            try:
                incident = Incident.objects.create(
                    company=company,
                    title=incident_data['title'],
                    description=incident_data['description'],
                    severity=incident_data['severity'],
                    status=incident_data['status'],
                    affected_services=incident_data['affected_services'],
                    error_logs=incident_data['error_logs'],
                    monitoring_dashboard_url=incident_data['monitoring_dashboard_url'],
                    codebase_context=incident_data['codebase_context'],
                    time_limit_minutes=self._get_time_limit(incident_data['severity']),
                    assigned_user=user
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created incident: {incident.title}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating incident {incident_data["title"]}: {str(e)}')
                )
                skipped_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully imported {created_count} incidents. '
                f'Skipped {skipped_count} incidents.'
            )
        )
    
    def _get_time_limit(self, severity):
        """Get time limit based on severity"""
        time_limits = {
            'P0': 30,  # Critical - 30 minutes
            'P1': 60,  # High - 1 hour
            'P2': 120, # Medium - 2 hours
            'P3': 240  # Low - 4 hours
        }
        return time_limits.get(severity, 60)
