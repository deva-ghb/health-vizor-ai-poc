import os
import json
from typing import Dict, Any, Type, Union
from pydantic import BaseModel

from litellm import completion
import litellm

# Configure LiteLLM for Azure OpenAI
litellm.api_key = os.getenv("AZURE_OPENAI_API_KEY")
litellm.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
litellm.api_version = os.getenv("AZURE_OPENAI_API_VERSION")

def call_llm(model_name: str, messages: list, response_format: Type[BaseModel] = None, user_context=None) -> Union[Dict[str, Any], BaseModel]:
    """
    Calls Azure OpenAI and returns the parsed response with enhanced personalization.
    model_name: Azure OpenAI model name (e.g. 'azure/gpt-4o', 'azure/gpt-4o-mini', etc)
    messages: list of dicts (role/content)
    response_format: Optional Pydantic model class for structured output
    user_context: Optional dict with user personalization data
    """
    # Validate Azure OpenAI configuration
    if not os.environ.get("AZURE_OPENAI_API_KEY"):
        raise EnvironmentError("AZURE_OPENAI_API_KEY must be set in environment for Azure OpenAI.")
    if not os.environ.get("AZURE_OPENAI_ENDPOINT"):
        raise EnvironmentError("AZURE_OPENAI_ENDPOINT must be set in environment for Azure OpenAI.")
    
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
        # Configure Azure OpenAI specific parameters
        completion_params = {
            "model": model_name,
            "messages": personalized_messages,
            "temperature": 0.7 if user_context else 0.5,  # Slightly more creative for personalized responses
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION")
        }

        # Add structured output format if Pydantic model is provided
        if response_format and issubclass(response_format, BaseModel):
            # For Azure OpenAI, we need to use JSON mode and add schema instructions
            completion_params["response_format"] = {"type": "json_object"}

            # Add schema instruction to the last message
            schema_instruction = f"""
Please respond with a valid JSON object that matches this exact schema:

{response_format.model_json_schema()}

Ensure all required fields are included and the response is valid JSON.
"""
            # Append schema instruction to the last user message
            if personalized_messages and personalized_messages[-1]["role"] == "user":
                personalized_messages[-1]["content"] += "\n\n" + schema_instruction
            else:
                personalized_messages.append({"role": "user", "content": schema_instruction})

        response = completion(**completion_params)

        # Log cost and token usage to terminal
        try:
            cost = response._hidden_params.get("response_cost", 0.0)
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            user_name = user_context.get("name", "Unknown") if user_context else "Unknown"

            print(f"💰 LLM Cost: ${cost:.6f} | Model: {model_name} | User: {user_name}")
            print(f"📊 Tokens - Input: {prompt_tokens}, Output: {completion_tokens}, Total: {total_tokens}")
            print("-" * 80)
        except Exception as e:
            print(f"❌ Failed to log LLM cost: {str(e)}")

        # litellm returns a dict with 'choices', get the content from the first choice
        content = response["choices"][0]["message"]["content"]

        # If we have a Pydantic response format, try to parse into that model
        if response_format and issubclass(response_format, BaseModel):
            try:
                parsed_json = json.loads(content)

                # Enhance parsed response with personalization markers if user context exists
                if user_context and isinstance(parsed_json, dict):
                    user_name = user_context.get('name', 'User')
                    # Add personalized disclaimer if it exists in the schema
                    if 'disclaimer' in parsed_json:
                        parsed_json['disclaimer'] = f"{user_name}, these recommendations are specifically designed with your goals in mind. These recommendations are for educational purposes only and do not constitute medical advice. Please consult a healthcare provider before starting any new regimen."

                # Create Pydantic model instance
                model_instance = response_format(**parsed_json)
                return model_instance

            except (json.JSONDecodeError, ValueError) as e:
                # If parsing fails, return a fallback structured response
                user_name = user_context.get('name', 'User') if user_context else 'User'
                return {
                    "error": f"Failed to parse structured response: {str(e)}",
                    "raw_content": content,
                    "analysis_summary": f"Hi {user_name}, " + (content[:200] + "..." if len(content) > 200 else content),
                    "disclaimer": f"{user_name}, these recommendations are for educational purposes only and do not constitute medical advice. Please consult a healthcare provider before starting any new regimen.",
                    "_personalization_applied": bool(user_context)
                }
        else:
            # No structured format requested, try to parse as JSON or return as string
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