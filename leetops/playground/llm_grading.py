"""
LLM-based grading system for incident response training
Uses Groq API to evaluate user responses and provide concise feedback
"""

import os
import json
from groq import Groq
from typing import Dict, Any, Optional


class LLMGrader:
    def __init__(self):
        # Initialize Groq client
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        if not os.getenv('GROQ_API_KEY'):
            print("WARNING: GROQ_API_KEY not found in environment variables")
    
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
        Grade a user's incident response using Groq LLM
        
        Returns:
            Dict containing score (0-100) and concise feedback paragraph
        """
        
        # Create simplified prompt for Groq
        prompt = self._create_simplified_grading_prompt(
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
            # Call Groq API
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Fast and efficient model
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert incident response instructor. Rate the quality of the response out of 100 and provide concise, educational feedback like you're teaching best practices for incident response. First return the score of the numerical score of the response as the first characters. And then enter a line of 10 equals signs and underneath leave your educational feedback below there."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500  # Keep response concise
            )
            
            # Parse the response
            grading_result = self._parse_simplified_response(response.choices[0].message.content)
            
            return grading_result
            
        except Exception as e:
            print(f"Groq grading failed: {e}")
            # Fallback grading
            return self._fallback_simplified_grading(
                user_resolution_approach=user_resolution_approach,
                user_code_changes=user_code_changes,
                user_commands_executed=user_commands_executed,
                user_solution_type=user_solution_type,
                time_spent_minutes=time_spent_minutes,
                time_limit_minutes=time_limit_minutes,
                incident_severity=incident_severity,
                error=str(e)
            )
    
    def _create_simplified_grading_prompt(
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
        """Create a simplified prompt for Groq grading"""
        
        prompt = f"""
INCIDENT DETAILS:
Title: {incident_title}
Description: {incident_description}
Severity: {incident_severity}
Time Limit: {time_limit_minutes} minutes
Time Spent: {time_spent_minutes} minutes

INCIDENT CONTEXT:
Affected Services: {incident_context.get('affected_services', 'N/A')}
Error Logs: {incident_context.get('error_logs', 'N/A')}
Codebase Context: {incident_context.get('codebase_context', 'N/A')}

USER'S RESPONSE:
Resolution Approach: {user_resolution_approach}
Code Changes: {user_code_changes}
Commands Executed: {', '.join(user_commands_executed) if user_commands_executed else 'None'}
Solution Type: {user_solution_type}

Please provide:
1. A score out of 100 (0-100)
2. A concise paragraph of feedback teaching best practices for incident response
"""
        return prompt
    
    def _parse_simplified_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the simplified Groq response"""
        try:
            lines = response_text.strip().split('\n')
            score = 50  # Default score
            feedback = "Unable to parse feedback from LLM response."
            
            # Look for the score at the beginning of the response
            if lines:
                first_line = lines[0].strip()
                # Try to extract score from first line (could be just a number or have text)
                try:
                    # Look for any number in the first line
                    import re
                    score_match = re.search(r'\b(\d{1,3})\b', first_line)
                    if score_match:
                        score = int(score_match.group(1))
                        score = max(0, min(100, score))  # Clamp between 0-100
                except ValueError:
                    score = 50
            
            # Look for the feedback after the equals signs
            feedback_lines = []
            found_equals = False
            
            for line in lines:
                if '=' in line and len(line.strip().replace('=', '')) == 0:
                    # Found the equals separator
                    found_equals = True
                    continue
                elif found_equals and line.strip():
                    # Collect feedback lines after equals
                    feedback_lines.append(line.strip())
            
            if feedback_lines:
                feedback = ' '.join(feedback_lines)
            
            return {
                'score': score,
                'feedback': feedback,
                'grading_method': 'groq'
            }
            
        except Exception as e:
            print(f"Error parsing Groq response: {e}")
            return {
                'score': 50,
                'feedback': "Error parsing LLM response. Please try again.",
                'grading_method': 'groq_parse_error'
            }
    
    def _fallback_simplified_grading(
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
        """Fallback grading when Groq is unavailable"""
        
        # Basic scoring based on solution type and time efficiency
        base_score = 50
        
        if user_solution_type == 'root_cause':
            base_score = 80
        elif user_solution_type == 'workaround':
            base_score = 60
        elif user_solution_type == 'escalation':
            base_score = 40
        else:
            base_score = 30
        
        # Adjust for time efficiency
        if time_limit_minutes > 0:
            time_ratio = time_spent_minutes / time_limit_minutes
            if time_ratio <= 0.5:
                base_score += 10
            elif time_ratio <= 0.75:
                base_score += 5
            elif time_ratio > 1.0:
                base_score -= 10
        
        # Clamp score
        final_score = max(0, min(100, base_score))
        
        feedback = f"Fallback grading applied due to LLM unavailability. "
        if user_solution_type == 'root_cause':
            feedback += "Good job identifying the root cause! In real incidents, always verify your fix thoroughly and monitor the system afterward."
        elif user_solution_type == 'workaround':
            feedback += "Workarounds are acceptable for immediate relief, but remember to follow up with a proper root cause fix to prevent recurrence."
        else:
            feedback += "Consider reviewing incident response best practices: assess impact, gather information, implement a fix, and verify resolution."
        
        return {
            'score': final_score,
            'feedback': feedback,
            'grading_method': 'fallback'
        }


# Global instance
llm_grader = LLMGrader()