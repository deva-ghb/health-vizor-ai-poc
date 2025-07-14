import os
import json
from typing import Dict, Any

from litellm import completion

def call_llm(model_name: str, messages: list, response_format=None, user_context=None) -> Dict[str, Any]:
    """
    Calls the selected LLM and returns the parsed response with enhanced personalization.
    model_name: exact model name string (e.g. 'gpt-4.1', 'gemini/gemini-pro', etc)
    messages: list of dicts (role/content)
    response_format: Optional, for OpenAI
    user_context: Optional dict with user personalization data
    """
    # Gemini models require GEMINI_API_KEY
    if model_name.startswith("gemini/") or model_name.startswith("gemini-"):
        if not os.environ.get("GEMINI_API_KEY"):
            raise EnvironmentError("GEMINI_API_KEY must be set in environment for Gemini models.")
    
    # Add personalization system message if user context is provided
    if user_context:
        personalization_prompt = f"""
PERSONALIZATION CONTEXT: You are responding to {user_context.get('name', 'this user')}. 
Communication Style: {user_context.get('communication_style', 'encouraging')}
Focus Areas: {', '.join(user_context.get('focus_areas', []))}
Interaction #: {user_context.get('interaction_count', 1)}
Previous Preferences: {user_context.get('preferences_summary', 'None yet')}

Remember to use their name frequently and make every response feel personally crafted for them.
"""
        # Insert system message at the beginning
        personalized_messages = [{"role": "system", "content": personalization_prompt}] + messages
    else:
        personalized_messages = messages
    
    try:
        response = completion(
            model=model_name,
            messages=personalized_messages,
            response_format=response_format,
            temperature=0.7 if user_context else 0.5  # Slightly more creative for personalized responses
        )
        # litellm returns a dict with 'choices', get the content from the first choice
        content = response["choices"][0]["message"]["content"]
        
        # Try to parse as JSON, if it fails, return as string
        try:
            parsed_response = json.loads(content)
            
            # Enhance parsed response with personalization markers if user context exists
            if user_context and isinstance(parsed_response, dict):
                user_name = user_context.get('name', 'User')
                # Add personalized disclaimer
                if 'disclaimer' in parsed_response:
                    parsed_response['disclaimer'] = f"{user_name}, these recommendations are specifically designed with your goals in mind. These recommendations are for educational purposes only and do not constitute medical advice. Please consult a healthcare provider before starting any new regimen."
                
                # Mark response as personalized
                parsed_response['_personalization_applied'] = True
                parsed_response['_user_name'] = user_name
                parsed_response['_interaction_count'] = user_context.get('interaction_count', 1)
                
            return parsed_response
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return as a structured response
            user_name = user_context.get('name', 'User') if user_context else 'User'
            return {
                "analysis_summary": f"Hi {user_name}, " + (content[:200] + "..." if len(content) > 200 else content),
                "insights": [content],
                "recommendations": None,
                "disclaimer": f"{user_name}, these recommendations are for educational purposes only and do not constitute medical advice. Please consult a healthcare provider before starting any new regimen.",
                "_personalization_applied": bool(user_context)
            }
    except Exception as e:
        raise Exception(f"LLM call failed for model {model_name}: {str(e)}") 