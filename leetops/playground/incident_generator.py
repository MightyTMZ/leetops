"""
LLM-powered incident generation system for LeetOps
Generates realistic production incidents based on company context
"""

import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from django.utils import timezone

# Company-specific incident templates
COMPANY_INCIDENT_TEMPLATES = {
    "amazon": {
        "focus_areas": ["distributed-systems", "aws-services", "scalability"],
        "common_services": ["EC2", "S3", "Lambda", "RDS", "DynamoDB", "CloudFront"],
        "incident_types": [
            {
                "title": "S3 Bucket Access Denied",
                "description": "Multiple services reporting 403 errors when accessing S3 buckets. Customer uploads failing.",
                "severity": "P1",
                "time_limit": 30,
                "affected_services": ["user-uploads", "media-processing", "cdn"],
                "error_logs": """2024-01-15 10:30:15 ERROR [s3-client] AccessDenied: Access Denied
2024-01-15 10:30:16 ERROR [upload-service] Failed to store file: s3://bucket/uploads/file.jpg
2024-01-15 10:30:17 ERROR [media-processor] Cannot access S3 bucket: access denied""",
                "codebase_context": "S3Client class in aws_utils.py handles bucket operations"
            },
            {
                "title": "Lambda Cold Start Storm",
                "description": "API response times spiking due to Lambda cold starts. 95th percentile latency > 10s.",
                "severity": "P2",
                "time_limit": 45,
                "affected_services": ["api-gateway", "user-service", "notification-service"],
                "error_logs": """2024-01-15 11:15:22 WARN [lambda-runtime] Cold start detected: 8.5s init time
2024-01-15 11:15:23 WARN [api-gateway] Request timeout after 10s
2024-01-15 11:15:24 ERROR [user-service] Function timeout exceeded""",
                "codebase_context": "Lambda functions in /src/lambda/ directory"
            }
        ]
    },
    "google": {
        "focus_areas": ["search", "ml", "distributed-systems", "big-data"],
        "common_services": ["Search", "Gmail", "YouTube", "Maps", "Ads"],
        "incident_types": [
            {
                "title": "Search Index Corruption",
                "description": "Search results returning outdated or missing content. Index replication failing.",
                "severity": "P0",
                "time_limit": 60,
                "affected_services": ["search-indexer", "query-processor", "result-cache"],
                "error_logs": """2024-01-15 09:45:12 ERROR [indexer] Failed to replicate index shard 42
2024-01-15 09:45:13 ERROR [query-processor] Index checksum mismatch detected
2024-01-15 09:45:14 WARN [search-api] Returning stale results due to index issues""",
                "codebase_context": "Index management in /search/index/ directory"
            },
            {
                "title": "ML Model Performance Degradation",
                "description": "Recommendation accuracy dropping by 15%. Model serving latency increased.",
                "severity": "P1",
                "time_limit": 90,
                "affected_services": ["ml-serving", "recommendation-engine", "feature-store"],
                "error_logs": """2024-01-15 14:20:33 WARN [ml-serving] Model prediction time: 245ms (normally 80ms)
2024-01-15 14:20:34 ERROR [recommendation-engine] Feature vector missing key attributes
2024-01-15 14:20:35 WARN [feature-store] Cache hit rate dropped to 45%""",
                "codebase_context": "ML models in /ml/models/ and serving code in /ml/serving/"
            }
        ]
    },
    "meta": {
        "focus_areas": ["social-platform", "real-time", "mobile", "content-moderation"],
        "common_services": ["NewsFeed", "Messenger", "Instagram", "WhatsApp"],
        "incident_types": [
            {
                "title": "News Feed Algorithm Outage",
                "description": "Users seeing empty feeds or outdated posts. Content ranking service down.",
                "severity": "P0",
                "time_limit": 45,
                "affected_services": ["feed-service", "ranking-engine", "content-cache"],
                "error_logs": """2024-01-15 16:30:45 ERROR [feed-service] Failed to fetch user timeline
2024-01-15 16:30:46 ERROR [ranking-engine] Service unavailable: connection timeout
2024-01-15 16:30:47 WARN [content-cache] Cache miss rate: 95% (normal: 15%)""",
                "codebase_context": "Feed generation logic in /src/feed/ directory"
            },
            {
                "title": "Real-time Message Delivery Failure",
                "description": "Messenger messages not being delivered in real-time. WebSocket connections dropping.",
                "severity": "P1",
                "time_limit": 30,
                "affected_services": ["messenger-api", "websocket-gateway", "notification-service"],
                "error_logs": """2024-01-15 18:15:22 ERROR [websocket-gateway] Connection pool exhausted
2024-01-15 18:15:23 ERROR [messenger-api] Message delivery timeout: 30s
2024-01-15 18:15:24 WARN [notification-service] Push notification queue backing up""",
                "codebase_context": "Real-time messaging in /src/messaging/ directory"
            }
        ]
    },
    "uber": {
        "focus_areas": ["location-services", "matching-algorithms", "real-time", "mobile"],
        "common_services": ["Matching", "Location", "Payment", "Driver", "Rider"],
        "incident_types": [
            {
                "title": "Driver-Rider Matching Algorithm Failure",
                "description": "Riders unable to find drivers. Matching service returning empty results.",
                "severity": "P0",
                "time_limit": 25,
                "affected_services": ["matching-service", "location-service", "driver-api"],
                "error_logs": """2024-01-15 19:45:12 ERROR [matching-service] No drivers found in 5km radius
2024-01-15 19:45:13 ERROR [location-service] GPS accuracy below threshold
2024-01-15 19:45:14 WARN [driver-api] Driver location updates delayed by 2+ minutes""",
                "codebase_context": "Matching algorithms in /src/matching/ directory"
            },
            {
                "title": "Surge Pricing Calculation Error",
                "description": "Surge pricing showing incorrect multipliers. Revenue impact detected.",
                "severity": "P1",
                "time_limit": 40,
                "affected_services": ["pricing-service", "demand-calculator", "payment-processor"],
                "error_logs": """2024-01-15 20:30:15 ERROR [pricing-service] Surge multiplier calculation failed
2024-01-15 20:30:16 WARN [demand-calculator] Historical data missing for time window
2024-01-15 20:30:17 ERROR [payment-processor] Price validation failed: 300% surge""",
                "codebase_context": "Pricing logic in /src/pricing/ directory"
            }
        ]
    },
    "coinbase": {
        "focus_areas": ["trading-systems", "security", "blockchain", "financial-compliance"],
        "common_services": ["Trading", "Wallet", "Exchange", "Security", "Compliance"],
        "incident_types": [
            {
                "title": "Trading Engine Performance Degradation",
                "description": "Order execution delays causing slippage. Trade volume dropping.",
                "severity": "P0",
                "time_limit": 20,
                "affected_services": ["trading-engine", "order-book", "market-data"],
                "error_logs": """2024-01-15 13:25:33 ERROR [trading-engine] Order execution time: 2.5s (SLA: 100ms)
2024-01-15 13:25:34 WARN [order-book] Depth calculation timeout
2024-01-15 13:25:35 ERROR [market-data] Price feed lag: 15 seconds""",
                "codebase_context": "Trading engine in /src/trading/ directory"
            },
            {
                "title": "Wallet Balance Sync Issue",
                "description": "User balances showing incorrect amounts. Blockchain sync failing.",
                "severity": "P1",
                "time_limit": 60,
                "affected_services": ["wallet-service", "blockchain-sync", "balance-calculator"],
                "error_logs": """2024-01-15 15:40:22 ERROR [blockchain-sync] Failed to sync block 18543291
2024-01-15 15:40:23 ERROR [wallet-service] Balance calculation timeout
2024-01-15 15:40:24 WARN [balance-calculator] Inconsistent state detected""",
                "codebase_context": "Wallet management in /src/wallet/ directory"
            }
        ]
    },
    "shopify": {
        "focus_areas": ["e-commerce", "payment-processing", "inventory", "scalability"],
        "common_services": ["Checkout", "Inventory", "Payment", "Shipping", "Analytics"],
        "incident_types": [
            {
                "title": "Checkout Service 500 Errors",
                "description": "Customers unable to complete purchases. Payment processing failing.",
                "severity": "P0",
                "time_limit": 30,
                "affected_services": ["checkout-service", "payment-gateway", "order-processor"],
                "error_logs": """2024-01-15 11:20:15 ERROR [checkout-service] Internal server error during payment
2024-01-15 11:20:16 ERROR [payment-gateway] Connection timeout to Stripe API
2024-01-15 11:20:17 WARN [order-processor] Failed to create order: payment validation error""",
                "codebase_context": "Checkout flow in /src/checkout/ directory"
            },
            {
                "title": "Inventory Sync Delays",
                "description": "Product availability showing stale data. Inventory updates delayed.",
                "severity": "P2",
                "time_limit": 60,
                "affected_services": ["inventory-service", "product-catalog", "sync-engine"],
                "error_logs": """2024-01-15 14:35:22 WARN [inventory-service] Sync lag: 45 minutes
2024-01-15 14:35:23 ERROR [sync-engine] Failed to update 1,247 products
2024-01-15 14:35:24 WARN [product-catalog] Stale inventory data detected""",
                "codebase_context": "Inventory management in /src/inventory/ directory"
            }
        ]
    }
}


class IncidentGenerator:
    """Generates realistic incidents for LeetOps simulations"""
    
    def __init__(self, company_name: str):
        self.company_name = company_name.lower()
        self.templates = COMPANY_INCIDENT_TEMPLATES.get(self.company_name, self._get_default_templates())
    
    def _get_default_templates(self):
        """Fallback templates for companies not in the predefined list"""
        return {
            "focus_areas": ["web-services", "api", "database"],
            "common_services": ["api", "database", "cache", "auth"],
            "incident_types": [
                {
                    "title": "API Rate Limiting Issues",
                    "description": "API returning 429 errors. Rate limiting configuration needs adjustment.",
                    "severity": "P1",
                    "time_limit": 30,
                    "affected_services": ["api-gateway", "rate-limiter"],
                    "error_logs": """2024-01-15 10:15:22 ERROR [api-gateway] Rate limit exceeded: 1000 req/min
2024-01-15 10:15:23 ERROR [rate-limiter] Token bucket empty""",
                    "codebase_context": "Rate limiting configuration in api_config.py"
                },
                {
                    "title": "Database Connection Pool Exhaustion",
                    "description": "Application unable to connect to database. Connection pool at capacity.",
                    "severity": "P0",
                    "time_limit": 25,
                    "affected_services": ["database", "connection-pool"],
                    "error_logs": """2024-01-15 09:30:15 ERROR [database] Connection pool exhausted
2024-01-15 09:30:16 ERROR [app] Failed to acquire database connection""",
                    "codebase_context": "Database configuration in db_config.py"
                }
            ]
        }
    
    def generate_incident(self, severity: str = None, time_of_day: str = None) -> Dict[str, Any]:
        """Generate a random incident based on company context"""
        
        # Select incident template
        available_incidents = self.templates["incident_types"]
        
        # Filter by severity if specified
        if severity:
            available_incidents = [inc for inc in available_incidents if inc["severity"] == severity]
        
        if not available_incidents:
            available_incidents = self.templates["incident_types"]
        
        incident_template = random.choice(available_incidents)
        
        # Customize incident based on time of day
        customized_incident = self._customize_for_time_of_day(incident_template, time_of_day)
        
        # Add monitoring dashboard URL
        customized_incident["monitoring_dashboard_url"] = self._generate_monitoring_url()
        
        return customized_incident
    
    def _customize_for_time_of_day(self, incident: Dict[str, Any], time_of_day: str) -> Dict[str, Any]:
        """Customize incident details based on time of day"""
        customized = incident.copy()
        
        if time_of_day == "morning":
            # Morning incidents often involve overnight batch jobs or user login issues
            customized["description"] += " This issue was first reported during peak morning login hours."
        elif time_of_day == "afternoon":
            # Afternoon incidents often involve API performance or scaling issues
            customized["description"] += " Performance degradation noticed during afternoon traffic spike."
        elif time_of_day == "evening":
            # Evening incidents often involve deployment issues or end-of-day processing
            customized["description"] += " Issue appeared after recent deployment in the evening."
        
        return customized
    
    def _generate_monitoring_url(self) -> str:
        """Generate a mock monitoring dashboard URL"""
        dashboards = [
            "https://monitoring.example.com/dashboard/overview",
            "https://grafana.company.com/d/incident-response",
            "https://datadog.com/dashboard/incidents",
            "https://newrelic.com/dashboard/alerts",
            "https://splunk.company.com/en-US/app/search/incident_monitoring"
        ]
        return random.choice(dashboards)
    
    def generate_incident_schedule(self, work_hours: tuple = (9, 17), num_incidents: int = None) -> List[Dict[str, Any]]:
        """Generate a schedule of incidents throughout a work day"""
        
        if num_incidents is None:
            # Generate 3-6 incidents per day based on company incident frequency
            base_frequency = self.templates.get("incident_frequency", 0.1)
            num_incidents = random.randint(max(2, int(base_frequency * 8)), 6)
        
        incidents = []
        start_hour, end_hour = work_hours
        
        # Generate random times throughout the day
        incident_times = []
        for _ in range(num_incidents):
            hour = random.randint(start_hour, end_hour - 1)
            minute = random.randint(0, 59)
            incident_times.append((hour, minute))
        
        incident_times.sort()
        
        # Generate incidents for each time slot
        for i, (hour, minute) in enumerate(incident_times):
            time_of_day = self._get_time_of_day(hour)
            severity = self._get_severity_for_time(hour)
            
            incident = self.generate_incident(severity=severity, time_of_day=time_of_day)
            incident["scheduled_time"] = f"{hour:02d}:{minute:02d}"
            incident["sequence_number"] = i + 1
            
            incidents.append(incident)
        
        return incidents
    
    def _get_time_of_day(self, hour: int) -> str:
        """Determine time of day category based on hour"""
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        else:
            return "evening"
    
    def _get_severity_for_time(self, hour: int) -> str:
        """Get severity based on time of day (more critical issues during business hours)"""
        if 9 <= hour <= 17:  # Business hours
            return random.choices(["P0", "P1", "P2"], weights=[0.2, 0.4, 0.4])[0]
        else:  # Off hours
            return random.choices(["P1", "P2", "P3"], weights=[0.3, 0.5, 0.2])[0]


def create_company_data():
    """Create initial company data for the database"""
    companies_data = [
        {
            "name": "Amazon",
            "slug": "amazon",
            "description": "Global e-commerce and cloud computing giant. Focus on AWS services, distributed systems, and massive scale.",
            "industry": "Technology",
            "company_size": "Enterprise",
            "tech_stack": ["AWS", "Java", "Python", "DynamoDB", "Lambda", "S3"],
            "focus_areas": ["distributed-systems", "aws-services", "scalability"],
            "incident_frequency": 0.15,
            "severity_distribution": {"P0": 0.1, "P1": 0.3, "P2": 0.5, "P3": 0.1}
        },
        {
            "name": "Google",
            "slug": "google",
            "description": "Search engine and technology company. Focus on search algorithms, ML systems, and global infrastructure.",
            "industry": "Technology",
            "company_size": "Enterprise",
            "tech_stack": ["C++", "Python", "Go", "Kubernetes", "TensorFlow", "BigQuery"],
            "focus_areas": ["search", "ml", "distributed-systems", "big-data"],
            "incident_frequency": 0.12,
            "severity_distribution": {"P0": 0.15, "P1": 0.25, "P2": 0.5, "P3": 0.1}
        },
        {
            "name": "Meta",
            "slug": "meta",
            "description": "Social media and technology company. Focus on real-time systems, social platforms, and mobile applications.",
            "industry": "Technology",
            "company_size": "Enterprise",
            "tech_stack": ["React", "PHP", "Python", "Hack", "C++", "GraphQL"],
            "focus_areas": ["social-platform", "real-time", "mobile", "content-moderation"],
            "incident_frequency": 0.18,
            "severity_distribution": {"P0": 0.2, "P1": 0.35, "P2": 0.4, "P3": 0.05}
        },
        {
            "name": "Uber",
            "slug": "uber",
            "description": "Ridesharing and delivery platform. Focus on location services, matching algorithms, and real-time systems.",
            "industry": "Transportation",
            "company_size": "Large",
            "tech_stack": ["Python", "Go", "Java", "PostgreSQL", "Redis", "Kafka"],
            "focus_areas": ["location-services", "matching-algorithms", "real-time", "mobile"],
            "incident_frequency": 0.2,
            "severity_distribution": {"P0": 0.25, "P1": 0.4, "P2": 0.3, "P3": 0.05}
        },
        {
            "name": "Coinbase",
            "slug": "coinbase",
            "description": "Cryptocurrency exchange platform. Focus on trading systems, security, and financial compliance.",
            "industry": "Fintech",
            "company_size": "Large",
            "tech_stack": ["Go", "Python", "React", "PostgreSQL", "Redis", "Docker"],
            "focus_areas": ["trading-systems", "security", "blockchain", "financial-compliance"],
            "incident_frequency": 0.08,
            "severity_distribution": {"P0": 0.3, "P1": 0.4, "P2": 0.25, "P3": 0.05}
        },
        {
            "name": "Shopify",
            "slug": "shopify",
            "description": "E-commerce platform for online stores. Focus on payment processing, inventory management, and scalability.",
            "industry": "E-commerce",
            "company_size": "Large",
            "tech_stack": ["Ruby", "JavaScript", "React", "MySQL", "Redis", "Kubernetes"],
            "focus_areas": ["e-commerce", "payment-processing", "inventory", "scalability"],
            "incident_frequency": 0.16,
            "severity_distribution": {"P0": 0.2, "P1": 0.35, "P2": 0.4, "P3": 0.05}
        },
        {
            "name": "Bloomberg",
            "slug": "bloomberg",
            "description": "Financial data and news company. Focus on real-time data processing, terminal systems, and financial APIs.",
            "industry": "Finance",
            "company_size": "Large",
            "tech_stack": ["C++", "Python", "Java", "Oracle", "Kafka", "Redis"],
            "focus_areas": ["financial-data", "real-time-processing", "terminal-systems", "data-feeds"],
            "incident_frequency": 0.1,
            "severity_distribution": {"P0": 0.25, "P1": 0.35, "P2": 0.35, "P3": 0.05}
        },
        {
            "name": "RBC",
            "slug": "rbc",
            "description": "Canadian multinational bank. Focus on banking systems, compliance, and financial services.",
            "industry": "Banking",
            "company_size": "Enterprise",
            "tech_stack": ["Java", "C#", "Python", "Oracle", "IBM MQ", "Mainframe"],
            "focus_areas": ["banking-systems", "compliance", "financial-services", "security"],
            "incident_frequency": 0.06,
            "severity_distribution": {"P0": 0.4, "P1": 0.4, "P2": 0.15, "P3": 0.05}
        }
    ]
    
    return companies_data
