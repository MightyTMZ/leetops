"""
Assessment Engine for LeetOps
Validates incident resolution solutions and determines quality scores
"""

import re
import json
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime


class SolutionValidator:
    """
    Validates incident resolution solutions based on multiple criteria
    """
    
    def __init__(self):
        self.validation_patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, List[str]]:
        """Initialize regex patterns for common solution validations"""
        
        return {
            'database_issues': [
                r'(?i)(ALTER TABLE|CREATE INDEX|DROP INDEX|VACUUM|ANALYZE)',
                r'(?i)(connection pool|connection limit|max_connections)',
                r'(?i)(query optimization|slow query|index)',
                r'(?i)(restart.*service|restart.*database)'
            ],
            'memory_issues': [
                r'(?i)(memory leak|garbage collection|GC)',
                r'(?i)(heap dump|memory dump|outofmemory)',
                r'(?i)(increase.*memory|memory.*limit)',
                r'(?i)(restart.*application|restart.*service)'
            ],
            'network_issues': [
                r'(?i)(timeout|connection.*refused|network.*error)',
                r'(?i)(DNS|resolve.*hostname|ping|telnet)',
                r'(?i)(firewall|security.*group|network.*acl)',
                r'(?i)(load.*balancer|proxy|reverse.*proxy)'
            ],
            'deployment_issues': [
                r'(?i)(rollback|deploy|release|version)',
                r'(?i)(config.*change|environment.*variable)',
                r'(?i)(restart.*service|restart.*container)',
                r'(?i)(git.*revert|git.*reset)'
            ],
            'ssl_certificate_issues': [
                r'(?i)(ssl.*certificate|cert.*expired|openssl)',
                r'(?i)(renew.*cert|update.*cert)',
                r'(?i)(https.*error|ssl.*error)'
            ]
        }
    
    def validate_solution(
        self,
        incident_type: str,
        resolution_approach: str,
        code_changes: str,
        commands_executed: List[str],
        affected_services: List[str]
    ) -> Dict[str, Any]:
        """
        Validate a solution based on incident type and provided information
        
        Args:
            incident_type: Type of incident (e.g., 'database', 'memory', 'network')
            resolution_approach: Text description of the resolution approach
            code_changes: Code changes made (if any)
            commands_executed: List of commands executed
            affected_services: List of services affected by the incident
            
        Returns:
            Validation result with quality score and feedback
        """
        
        validation_result = {
            'is_valid': False,
            'quality_score': 0.0,
            'solution_type': 'unknown',
            'feedback': [],
            'strengths': [],
            'weaknesses': [],
            'suggestions': []
        }
        
        # Analyze resolution approach
        approach_analysis = self._analyze_resolution_approach(
            resolution_approach, incident_type
        )
        
        # Analyze code changes
        code_analysis = self._analyze_code_changes(code_changes, incident_type)
        
        # Analyze commands
        command_analysis = self._analyze_commands(commands_executed, incident_type)
        
        # Combine analyses
        validation_result.update(approach_analysis)
        validation_result['code_analysis'] = code_analysis
        validation_result['command_analysis'] = command_analysis
        
        # Calculate overall quality score
        validation_result['quality_score'] = self._calculate_quality_score(
            approach_analysis, code_analysis, command_analysis
        )
        
        # Determine if solution is valid
        validation_result['is_valid'] = validation_result['quality_score'] >= 0.6
        
        return validation_result
    
    def _analyze_resolution_approach(
        self, 
        approach: str, 
        incident_type: str
    ) -> Dict[str, Any]:
        """Analyze the resolution approach text"""
        
        analysis = {
            'approach_quality': 0.0,
            'indicates_root_cause': False,
            'indicates_workaround': False,
            'approach_feedback': []
        }
        
        approach_lower = approach.lower()
        
        # Check for root cause indicators
        root_cause_indicators = [
            'root cause', 'underlying issue', 'fix the problem',
            'permanent solution', 'address the cause'
        ]
        
        workaround_indicators = [
            'workaround', 'temporary fix', 'quick fix',
            'band-aid', 'stopgap', 'mitigation'
        ]
        
        # Analyze approach quality
        if any(indicator in approach_lower for indicator in root_cause_indicators):
            analysis['indicates_root_cause'] = True
            analysis['approach_quality'] += 0.4
            analysis['approach_feedback'].append("Good: Identifies root cause approach")
        
        if any(indicator in approach_lower for indicator in workaround_indicators):
            analysis['indicates_workaround'] = True
            analysis['approach_quality'] += 0.2
            analysis['approach_feedback'].append("Note: Using workaround approach")
        
        # Check for technical depth
        technical_terms = [
            'configuration', 'parameter', 'setting', 'environment',
            'service', 'database', 'cache', 'memory', 'network'
        ]
        
        technical_depth = sum(1 for term in technical_terms if term in approach_lower)
        analysis['approach_quality'] += min(0.3, technical_depth * 0.05)
        
        if technical_depth > 3:
            analysis['approach_feedback'].append("Good: Shows technical understanding")
        
        # Check for prevention measures
        prevention_indicators = [
            'prevent', 'monitoring', 'alert', 'automation',
            'improvement', 'better', 'enhance'
        ]
        
        if any(indicator in approach_lower for indicator in prevention_indicators):
            analysis['approach_quality'] += 0.2
            analysis['approach_feedback'].append("Excellent: Considers prevention")
        
        # Determine solution type
        if analysis['indicates_root_cause']:
            analysis['solution_type'] = 'root_cause'
        elif analysis['indicates_workaround']:
            analysis['solution_type'] = 'workaround'
        else:
            analysis['solution_type'] = 'unclear'
        
        return analysis
    
    def _analyze_code_changes(self, code_changes: str, incident_type: str) -> Dict[str, Any]:
        """Analyze code changes made"""
        
        analysis = {
            'has_code_changes': bool(code_changes.strip()),
            'code_quality': 0.0,
            'code_feedback': [],
            'relevant_patterns': []
        }
        
        if not code_changes.strip():
            analysis['code_feedback'].append("No code changes provided")
            return analysis
        
        code_lower = code_changes.lower()
        
        # Check for relevant patterns based on incident type
        if incident_type in self.validation_patterns:
            patterns = self.validation_patterns[incident_type]
            matched_patterns = []
            
            for pattern in patterns:
                if re.search(pattern, code_changes, re.IGNORECASE):
                    matched_patterns.append(pattern)
            
            analysis['relevant_patterns'] = matched_patterns
            
            if matched_patterns:
                analysis['code_quality'] += 0.4
                analysis['code_feedback'].append(f"Good: Code addresses {incident_type} patterns")
            else:
                analysis['code_feedback'].append(f"Warning: Code may not address {incident_type} issues")
        
        # Check for code quality indicators
        quality_indicators = [
            'try', 'catch', 'error handling', 'logging',
            'validation', 'check', 'verify'
        ]
        
        quality_score = sum(1 for indicator in quality_indicators if indicator in code_lower)
        analysis['code_quality'] += min(0.3, quality_score * 0.1)
        
        if quality_score > 2:
            analysis['code_feedback'].append("Good: Includes error handling")
        
        # Check for comments/documentation
        if '//' in code_changes or '#' in code_changes or '/*' in code_changes:
            analysis['code_quality'] += 0.1
            analysis['code_feedback'].append("Good: Includes comments")
        
        return analysis
    
    def _analyze_commands(self, commands: List[str], incident_type: str) -> Dict[str, Any]:
        """Analyze commands executed"""
        
        analysis = {
            'command_count': len(commands),
            'command_quality': 0.0,
            'command_feedback': [],
            'relevant_commands': [],
            'potentially_dangerous': []
        }
        
        if not commands:
            analysis['command_feedback'].append("No commands executed")
            return analysis
        
        # Dangerous commands to flag
        dangerous_patterns = [
            r'(?i)(rm\s+-rf|delete.*all|drop.*database)',
            r'(?i)(kill\s+-9|pkill|killall)',
            r'(?i)(format|fdisk|mkfs)',
            r'(?i)(chmod\s+777|chown.*root)'
        ]
        
        for command in commands:
            command_lower = command.lower()
            
            # Check for dangerous commands
            for pattern in dangerous_patterns:
                if re.search(pattern, command):
                    analysis['potentially_dangerous'].append(command)
            
            # Check for relevant commands based on incident type
            if incident_type in self.validation_patterns:
                for pattern in self.validation_patterns[incident_type]:
                    if re.search(pattern, command, re.IGNORECASE):
                        analysis['relevant_commands'].append(command)
        
        # Calculate command quality
        if analysis['relevant_commands']:
            analysis['command_quality'] += 0.4
            analysis['command_feedback'].append("Good: Commands address incident type")
        
        if analysis['command_count'] > 0:
            analysis['command_quality'] += 0.2
            analysis['command_feedback'].append(f"Executed {analysis['command_count']} commands")
        
        # Check for diagnostic commands
        diagnostic_commands = ['grep', 'tail', 'head', 'cat', 'ps', 'top', 'netstat', 'ping']
        diagnostic_count = sum(1 for cmd in commands if any(diag in cmd.lower() for diag in diagnostic_commands))
        
        if diagnostic_count > 0:
            analysis['command_quality'] += 0.2
            analysis['command_feedback'].append("Good: Includes diagnostic commands")
        
        # Flag dangerous commands
        if analysis['potentially_dangerous']:
            analysis['command_quality'] -= 0.3
            analysis['command_feedback'].append("Warning: Potentially dangerous commands detected")
        
        return analysis
    
    def _calculate_quality_score(
        self, 
        approach_analysis: Dict[str, Any],
        code_analysis: Dict[str, Any], 
        command_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall quality score"""
        
        # Weight different components
        approach_weight = 0.5
        code_weight = 0.3
        command_weight = 0.2
        
        # Calculate weighted score
        score = (
            approach_analysis['approach_quality'] * approach_weight +
            code_analysis['code_quality'] * code_weight +
            command_analysis['command_quality'] * command_weight
        )
        
        # Bonus for root cause fixes
        if approach_analysis['solution_type'] == 'root_cause':
            score += 0.2
        
        # Penalty for dangerous commands
        if command_analysis['potentially_dangerous']:
            score -= 0.1
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))


class IncidentAssessmentEngine:
    """
    Main assessment engine that coordinates solution validation
    """
    
    def __init__(self):
        self.validator = SolutionValidator()
    
    def assess_incident_resolution(
        self,
        incident: Dict[str, Any],
        resolution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess an incident resolution attempt
        
        Args:
            incident: Incident information
            resolution_data: Resolution attempt data
            
        Returns:
            Comprehensive assessment result
        """
        
        # Determine incident type from title/description
        incident_type = self._classify_incident_type(incident)
        
        # Validate the solution
        validation_result = self.validator.validate_solution(
            incident_type=incident_type,
            resolution_approach=resolution_data.get('resolution_approach', ''),
            code_changes=resolution_data.get('code_changes', ''),
            commands_executed=resolution_data.get('commands_executed', []),
            affected_services=incident.get('affected_services', [])
        )
        
        # Generate overall assessment
        assessment = {
            'incident_type': incident_type,
            'validation_result': validation_result,
            'overall_quality': validation_result['quality_score'],
            'recommended_solution_type': self._recommend_solution_type(validation_result),
            'assessment_summary': self._generate_summary(validation_result),
            'improvement_suggestions': self._generate_improvements(validation_result),
            'assessment_timestamp': datetime.now().isoformat()
        }
        
        return assessment
    
    def _classify_incident_type(self, incident: Dict[str, Any]) -> str:
        """Classify incident type based on title and description"""
        
        title_lower = incident.get('title', '').lower()
        description_lower = incident.get('description', '').lower()
        text = f"{title_lower} {description_lower}"
        
        # Classification patterns
        type_patterns = {
            'database': ['database', 'db', 'sql', 'query', 'connection', 'timeout'],
            'memory': ['memory', 'oom', 'leak', 'heap', 'gc', 'garbage'],
            'network': ['network', 'connection', 'timeout', 'dns', 'firewall', 'ssl'],
            'deployment': ['deploy', 'release', 'version', 'config', 'environment'],
            'performance': ['slow', 'latency', 'performance', 'cpu', 'load'],
            'authentication': ['auth', 'login', 'token', 'credential', 'permission']
        }
        
        # Count matches for each type
        type_scores = {}
        for incident_type, patterns in type_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text)
            if score > 0:
                type_scores[incident_type] = score
        
        # Return the type with highest score
        if type_scores:
            return max(type_scores, key=type_scores.get)
        
        return 'general'
    
    def _recommend_solution_type(self, validation_result: Dict[str, Any]) -> str:
        """Recommend the best solution type based on validation"""
        
        if validation_result['quality_score'] >= 0.8:
            return 'root_cause'
        elif validation_result['quality_score'] >= 0.6:
            return 'workaround'
        else:
            return 'escalation'
    
    def _generate_summary(self, validation_result: Dict[str, Any]) -> str:
        """Generate a summary of the assessment"""
        
        quality_score = validation_result['quality_score']
        
        if quality_score >= 0.8:
            return "Excellent resolution with strong technical approach and comprehensive solution."
        elif quality_score >= 0.6:
            return "Good resolution with solid technical understanding and appropriate solution."
        elif quality_score >= 0.4:
            return "Adequate resolution with some technical merit but room for improvement."
        else:
            return "Poor resolution requiring significant improvement or escalation."
    
    def _generate_improvements(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions"""
        
        improvements = []
        
        if validation_result['quality_score'] < 0.6:
            improvements.append("Consider a more systematic approach to problem diagnosis")
        
        if not validation_result.get('indicates_root_cause', False):
            improvements.append("Focus on identifying and addressing the root cause rather than symptoms")
        
        if not validation_result['code_analysis']['has_code_changes']:
            improvements.append("Consider providing code changes or configuration updates")
        
        if not validation_result['command_analysis']['relevant_commands']:
            improvements.append("Include more relevant diagnostic and resolution commands")
        
        if validation_result['command_analysis']['potentially_dangerous']:
            improvements.append("Avoid potentially dangerous commands in production environments")
        
        return improvements
