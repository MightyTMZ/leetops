"""
LeetOps Demo Script
Demonstrates the core functionality of the LeetOps platform
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'leetops.settings')
django.setup()

from playground.models import Company, Incident, UserRating, SimulationSession, IncidentAttempt
from playground.incident_generator import IncidentGenerator
from playground.rating_calculator import RatingCalculator
from users.models import User


def create_demo_user():
    """Create a demo user for testing"""
    user, created = User.objects.get_or_create(
        email='demo@leetops.com',
        defaults={
            'username': 'demo_user',
            'first_name': 'Demo',
            'last_name': 'User',
            'is_active': True
        }
    )
    return user


def demo_incident_generation():
    """Demonstrate incident generation for different companies"""
    print("🚀 LeetOps Demo: Incident Generation")
    print("=" * 50)
    
    companies = Company.objects.all()[:3]  # Get first 3 companies
    
    for company in companies:
        print(f"\n📊 Company: {company.name}")
        print(f"   Industry: {company.industry}")
        print(f"   Tech Stack: {', '.join(company.tech_stack[:3])}...")
        
        generator = IncidentGenerator(company.name)
        
        # Generate a few incidents
        for i, severity in enumerate(['P0', 'P1', 'P2']):
            incident_data = generator.generate_incident(severity=severity)
            print(f"\n   🔥 Incident {i+1} ({severity}): {incident_data['title']}")
            print(f"      Description: {incident_data['description'][:80]}...")
            print(f"      Time Limit: {incident_data['time_limit']} minutes")
            print(f"      Affected Services: {', '.join(incident_data['affected_services'][:2])}...")


def demo_rating_calculation():
    """Demonstrate the rating calculation system"""
    print("\n\n📈 LeetOps Demo: Rating Calculation")
    print("=" * 50)
    
    # Test different resolution scenarios
    scenarios = [
        {
            'name': 'Excellent Resolution',
            'time_limit_minutes': 30,
            'actual_time_minutes': 8,  # Very fast
            'solution_type': 'root_cause',
            'severity': 'P0',
            'was_successful': True
        },
        {
            'name': 'Good Resolution',
            'time_limit_minutes': 30,
            'actual_time_minutes': 18,  # Good time
            'solution_type': 'workaround',
            'severity': 'P1',
            'was_successful': True
        },
        {
            'name': 'Poor Resolution',
            'time_limit_minutes': 30,
            'actual_time_minutes': 35,  # Over time limit
            'solution_type': 'escalation',
            'severity': 'P2',
            'was_successful': False
        },
        {
            'name': 'Abandoned',
            'time_limit_minutes': 30,
            'actual_time_minutes': 15,
            'solution_type': 'abandonment',
            'severity': 'P1',
            'was_successful': False
        }
    ]
    
    for scenario in scenarios:
        result = RatingCalculator.calculate_incident_rating(
            time_limit_minutes=scenario['time_limit_minutes'],
            actual_time_minutes=scenario['actual_time_minutes'],
            solution_type=scenario['solution_type'],
            severity=scenario['severity'],
            was_successful=scenario['was_successful'],
            was_escalated=(scenario['solution_type'] == 'escalation'),
            was_abandoned=(scenario['solution_type'] == 'abandonment')
        )
        
        print(f"\n🎯 {scenario['name']}")
        print(f"   Time: {scenario['actual_time_minutes']}/{scenario['time_limit_minutes']} min")
        print(f"   Solution: {scenario['solution_type']}")
        print(f"   Severity: {scenario['severity']}")
        print(f"   Points Earned: {result['total_points']}")
        if 'calculation_breakdown' in result and 'speed_category' in result['calculation_breakdown']:
            print(f"   Speed Category: {result['calculation_breakdown']['speed_category']}")
        print(f"   Quality Multiplier: {result['quality_multiplier']}x")


def demo_user_rating_progression():
    """Demonstrate user rating progression over multiple incidents"""
    print("\n\n👤 LeetOps Demo: User Rating Progression")
    print("=" * 50)
    
    user = create_demo_user()
    
    # Create or get user rating
    user_rating, created = UserRating.objects.get_or_create(user=user)
    print(f"Starting Rating: {user_rating.overall_rating}")
    print(f"Category: {RatingCalculator.get_rating_category(user_rating.overall_rating)}")
    
    # Simulate multiple incident attempts
    incident_results = []
    
    # Simulate a progression of incidents
    progression = [
        {'points': 25, 'description': 'First incident - learning'},
        {'points': 45, 'description': 'Getting better'},
        {'points': 60, 'description': 'Improving'},
        {'points': 35, 'description': 'Challenging incident'},
        {'points': 75, 'description': 'Excellent resolution'},
        {'points': 50, 'description': 'Consistent performance'},
    ]
    
    for i, result in enumerate(progression):
        incident_results.append({
            'total_points': result['points'],
            'calculation_breakdown': {
                'severity': 'P1',
                'time_limit': 30,
                'actual_time': 15,
                'solution_type': 'workaround'
            }
        })
        
        rating_update = RatingCalculator.update_user_rating(
            current_rating=user_rating.overall_rating,
            incident_results=incident_results
        )
        
        print(f"\n📊 Incident {i+1}: {result['description']}")
        print(f"   Points Earned: {result['points']}")
        print(f"   New Rating: {rating_update['new_rating']} (+{rating_update['rating_change']})")
        print(f"   Category: {RatingCalculator.get_rating_category(rating_update['new_rating'])}")
        print(f"   Success Rate: {rating_update['success_rate']:.1%}")
        
        # Update user rating
        user_rating.overall_rating = rating_update['new_rating']
        user_rating.save()
    
    # Final rating report
    final_report = RatingCalculator.generate_rating_report(
        user_rating.overall_rating, 
        incident_results
    )
    
    print(f"\n🏆 Final Rating Report")
    print(f"   Overall Rating: {final_report['current_rating']}")
    print(f"   Category: {final_report['category']}")
    print(f"   Percentile: {final_report['percentile']}%")
    print(f"   Points to Next Level: {final_report['points_to_next_category']}")


def demo_company_specific_incidents():
    """Demonstrate company-specific incident generation"""
    print("\n\n🏢 LeetOps Demo: Company-Specific Incidents")
    print("=" * 50)
    
    companies = ['amazon', 'google', 'meta', 'uber', 'coinbase']
    
    for company_name in companies:
        print(f"\n🏢 {company_name.upper()}")
        generator = IncidentGenerator(company_name)
        
        # Generate incident schedule for a work day
        schedule = generator.generate_incident_schedule(
            work_hours=(9, 17),
            num_incidents=3
        )
        
        for incident in schedule:
            print(f"\n   🚨 {incident['scheduled_time']} - {incident['severity']}")
            print(f"      {incident['title']}")
            print(f"      Time Limit: {incident['time_limit']} min")
            print(f"      Services: {', '.join(incident['affected_services'][:2])}...")


def main():
    """Run the complete LeetOps demo"""
    print("🎯 LeetOps: On-Call Engineer Rating Platform")
    print("=" * 60)
    print("The standardized benchmark for on-call engineering reliability")
    print("=" * 60)
    
    try:
        # Run all demos
        demo_incident_generation()
        demo_rating_calculation()
        demo_user_rating_progression()
        demo_company_specific_incidents()
        
        print("\n\n✅ LeetOps Demo Complete!")
        print("=" * 60)
        print("Key Features Demonstrated:")
        print("• Realistic incident generation for different companies")
        print("• Sophisticated rating calculation with speed/quality bonuses")
        print("• User rating progression tracking")
        print("• Company-specific incident patterns")
        print("• Time-pressured resolution simulation")
        print("\n🚀 Ready to revolutionize on-call engineering assessment!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
