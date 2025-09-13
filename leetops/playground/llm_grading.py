"""
LLM-based grading system for incident response training
Uses OpenAI API to evaluate user responses and provide detailed feedback
"""

import os
import json
import openai
from typing import Dict, Any, Optional
from django.conf import settings


class LLMGrader:
    def __init__(self):
        # Initialize OpenAI client
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
    
    def grade_incident_response(
        self,
        incident_title: str,
        incident_description: str,
        incident_severity: str,
        incident_context: Dict[str, Any],
        user_resolution_approach: str,
        user_code_changes: str,
        user_commands_executed: list,
        user_solution_type: str,
        time_spent_minutes: int,
        time_limit_minutes: int
    ) -> Dict[str, Any]:
        """
        Grade a user's incident response using LLM
        
        Args:
            incident_title: Title of the incident
            incident_description: Description of the incident
            incident_severity: Severity level (P0, P1, P2, P3)
            incident_context: Additional context (error logs, affected services, etc.)
            user_resolution_approach: User's description of their approach
            user_code_changes: Code changes made by user
            user_commands_executed: Commands executed by user
            user_solution_type: Type of solution (root_cause, workaround, etc.)
            time_spent_minutes: Time taken to resolve
            time_limit_minutes: Time limit for resolution
            
        Returns:
            Dict containing grade, feedback, and detailed analysis
        """
        
        # Prepare the grading prompt
        prompt = self._create_grading_prompt(
            incident_title=incident_title,
            incident_description=incident_description,
            incident_severity=incident_severity,
            incident_context=incident_context,
            user_resolution_approach=user_resolution_approach,
            user_code_changes=user_code_changes,
            user_commands_executed=user_commands_executed,
            user_solution_type=user_solution_type,
            time_spent_minutes=time_spent_minutes,
            time_limit_minutes=time_limit_minutes
        )
        
        try:
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert incident response engineer evaluating a junior engineer's performance. Provide detailed, constructive feedback and accurate scoring."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent grading
                max_tokens=1500
            )
            
            # Parse the response
            grading_result = self._parse_grading_response(response.choices[0].message.content)
            
            # Add metadata
            grading_result['grading_metadata'] = {
                'model_used': 'gpt-4',
                'time_spent_minutes': time_spent_minutes,
                'time_limit_minutes': time_limit_minutes,
                'time_efficiency': time_spent_minutes / time_limit_minutes if time_limit_minutes > 0 else 1.0,
                'solution_type': user_solution_type,
                'severity': incident_severity
            }
            
            return grading_result
            
        except Exception as e:
            # Fallback to rule-based grading if LLM fails
            return self._fallback_grading(
                user_resolution_approach=user_resolution_approach,
                user_code_changes=user_code_changes,
                user_commands_executed=user_commands_executed,
                user_solution_type=user_solution_type,
                time_spent_minutes=time_spent_minutes,
                time_limit_minutes=time_limit_minutes,
                incident_severity=incident_severity,
                error=str(e)
            )
    
    def _create_grading_prompt(
        self,
        incident_title: str,
        incident_description: str,
        incident_severity: str,
        incident_context: Dict[str, Any],
        user_resolution_approach: str,
        user_code_changes: str,
        user_commands_executed: list,
        user_solution_type: str,
        time_spent_minutes: int,
        time_limit_minutes: int
    ) -> str:
        """Create a detailed prompt for LLM grading"""
        
        prompt = f"""
You are evaluating an incident response engineer's performance. Please grade their response on a scale of 1-10 and provide detailed feedback.

INCIDENT DETAILS:
Title: {incident_title}
Severity: {incident_severity}
Description: {incident_description}

INCIDENT CONTEXT:
"""
        
        # Add context information
        if incident_context.get('affected_services'):
            prompt += f"Affected Services: {', '.join(incident_context['affected_services'])}\n"
        
        if incident_context.get('error_logs'):
            prompt += f"Error Logs:\n{incident_context['error_logs']}\n"
        
        if incident_context.get('codebase_context'):
            prompt += f"Codebase Context:\n{incident_context['codebase_context']}\n"
        
        prompt += f"""
TIME CONSTRAINTS:
Time Limit: {time_limit_minutes} minutes
Time Spent: {time_spent_minutes} minutes
Time Efficiency: {(time_spent_minutes/time_limit_minutes)*100:.1f}% of time limit used

USER'S RESPONSE:
Solution Type: {user_solution_type}
Resolution Approach: {user_resolution_approach}

Code Changes:
{user_code_changes if user_code_changes else "No code changes provided"}

Commands Executed:
{chr(10).join(f"- {cmd}" for cmd in user_commands_executed) if user_commands_executed else "No commands executed"}

GRADING CRITERIA:
Please evaluate based on these criteria (each worth 1-10 points):

1. TECHNICAL ACCURACY (1-10): Is the solution technically sound and likely to resolve the issue?
2. PROBLEM-SOLVING APPROACH (1-10): How well did they analyze the problem and develop a solution?
3. COMMUNICATION (1-10): How clear and detailed is their explanation of their approach?
4. EFFICIENCY (1-10): How efficiently did they use their time and resources?
5. BEST PRACTICES (1-10): Did they follow incident response best practices?

RESPONSE FORMAT:
Please respond with a JSON object containing:
{{
    "overall_score": <1-10>,
    "technical_accuracy": <1-10>,
    "problem_solving": <1-10>,
    "communication": <1-10>,
    "efficiency": <1-10>,
    "best_practices": <1-10>,
    "is_correct": <true/false>,
    "feedback": {{
        "strengths": ["strength1", "strength2"],
        "weaknesses": ["weakness1", "weakness2"],
        "suggestions": ["suggestion1", "suggestion2"],
        "overall_feedback": "Detailed overall feedback paragraph"
    }},
    "correctness_explanation": "Explanation of why the solution is correct or incorrect",
    "improvement_areas": ["area1", "area2"]
}}
"""
        
        return prompt
    
    def _parse_grading_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the LLM response into structured data"""
        
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                grading_data = json.loads(json_str)
                
                # Validate required fields
                required_fields = [
                    'overall_score', 'technical_accuracy', 'problem_solving',
                    'communication', 'efficiency', 'best_practices', 'is_correct'
                ]
                
                for field in required_fields:
                    if field not in grading_data:
                        raise ValueError(f"Missing required field: {field}")
                
                return grading_data
                
        except (json.JSONDecodeError, ValueError) as e:
            pass
        
        # Fallback parsing if JSON extraction fails
        return self._fallback_parse_response(response_text)
    
    def _fallback_parse_response(self, response_text: str) -> Dict[str, Any]:
        """Fallback parsing when JSON extraction fails"""
        
        # Extract scores using regex
        import re
        
        overall_score = 5  # Default score
        score_match = re.search(r'overall[_\s]*score[:\s]*(\d+)', response_text, re.IGNORECASE)
        if score_match:
            overall_score = int(score_match.group(1))
        
        # Determine if correct based on score
        is_correct = overall_score >= 6
        
        return {
            "overall_score": overall_score,
            "technical_accuracy": max(1, overall_score - 1),
            "problem_solving": max(1, overall_score),
            "communication": max(1, overall_score - 1),
            "efficiency": max(1, overall_score),
            "best_practices": max(1, overall_score - 1),
            "is_correct": is_correct,
            "feedback": {
                "strengths": ["Attempted to resolve the incident"],
                "weaknesses": ["Could improve technical approach"],
                "suggestions": ["Review incident response best practices"],
                "overall_feedback": response_text[:500] + "..." if len(response_text) > 500 else response_text
            },
            "correctness_explanation": "Solution evaluated based on overall score",
            "improvement_areas": ["Technical accuracy", "Problem-solving approach"]
        }
    
    def _fallback_grading(
        self,
        user_resolution_approach: str,
        user_code_changes: str,
        user_commands_executed: list,
        user_solution_type: str,
        time_spent_minutes: int,
        time_limit_minutes: int,
        incident_severity: str,
        error: str = None
    ) -> Dict[str, Any]:
        """Fallback rule-based grading when LLM is unavailable"""
        
        # Basic scoring based on solution type and time efficiency
        base_score = 5
        
        # Adjust score based on solution type
        if user_solution_type == 'root_cause':
            base_score += 2
        elif user_solution_type == 'workaround':
            base_score += 1
        elif user_solution_type == 'escalation':
            base_score -= 1
        elif user_solution_type == 'abandonment':
            base_score -= 3
        
        # Adjust score based on time efficiency
        time_efficiency = time_spent_minutes / time_limit_minutes if time_limit_minutes > 0 else 1.0
        if time_efficiency < 0.5:
            base_score += 1
        elif time_efficiency > 1.0:
            base_score -= 1
        
        # Adjust score based on response quality
        if user_resolution_approach and len(user_resolution_approach) > 50:
            base_score += 1
        
        if user_code_changes and len(user_code_changes) > 20:
            base_score += 1
        
        if user_commands_executed and len(user_commands_executed) > 0:
            base_score += 1
        
        # Clamp score to 1-10 range
        final_score = max(1, min(10, base_score))
        is_correct = final_score >= 6
        
        return {
            "overall_score": final_score,
            "technical_accuracy": max(1, final_score - 1),
            "problem_solving": max(1, final_score),
            "communication": max(1, final_score - 1),
            "efficiency": max(1, final_score),
            "best_practices": max(1, final_score - 1),
            "is_correct": is_correct,
            "feedback": {
                "strengths": ["Attempted to resolve the incident"],
                "weaknesses": ["Could improve technical approach"],
                "suggestions": ["Review incident response best practices"],
                "overall_feedback": f"Fallback grading applied due to LLM unavailability. Error: {error}" if error else "Fallback grading applied due to LLM unavailability."
            },
            "correctness_explanation": "Solution evaluated using rule-based fallback system",
            "improvement_areas": ["Technical accuracy", "Problem-solving approach"],
            "grading_method": "fallback",
            "grading_metadata": {
                'model_used': 'fallback',
                'time_spent_minutes': time_spent_minutes,
                'time_limit_minutes': time_limit_minutes,
                'time_efficiency': time_efficiency,
                'solution_type': user_solution_type,
                'severity': incident_severity,
                'error': error
            }
        }


# Global instance
llm_grader = LLMGrader()
