"""
Django management command to initialize company data for LeetOps
"""

from django.core.management.base import BaseCommand
from playground.models import Company
from playground.incident_generator import create_company_data


class Command(BaseCommand):
    help = 'Initialize company data for LeetOps platform'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing companies',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Initializing LeetOps companies...'))
        
        companies_data = create_company_data()
        created_count = 0
        updated_count = 0
        
        for company_data in companies_data:
            company, created = Company.objects.get_or_create(
                slug=company_data['slug'],
                defaults=company_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created company: {company.name}')
                )
            elif options['force']:
                # Update existing company
                for key, value in company_data.items():
                    if key != 'slug':  # Don't update slug
                        setattr(company, key, value)
                company.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated company: {company.name}')
                )
            else:
                self.stdout.write(
                    self.style.NOTICE(f'○ Company already exists: {company.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} companies, '
                f'updated {updated_count} companies.'
            )
        )
        
        total_companies = Company.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'Total companies in database: {total_companies}')
        )
