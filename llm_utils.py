import os
import json
from typing import Dict, Any, Type, Union
from pydantic import BaseModel
from datetime import datetime
import re

from litellm import completion

# Model configurations for different providers
MODEL_CONFIGS = {
    "azure/o1": {
        "api_key": "AZURE_OPENAI_API_KEY",
        "api_base": "AZURE_OPENAI_ENDPOINT",
        "api_version": "AZURE_OPENAI_API_VERSION",
        "deployment_name": "AZURE_OPENAI_DEPLOYMENT_NAME",
        "provider": "azure"
    },
    "azure/o4-mini": {
        "api_key": "AZURE_O4_MINI_API_KEY_NEW",
        "api_base": "AZURE_O4_MINI_ENDPOINT_NEW",
        "api_version": "AZURE_O4_MINI_API_VERSION_NEW",
        "deployment_name": "AZURE_O4_MINI_DEPLOYMENT_NAME_NEW",
        "provider": "azure"
    },
    "openai/o3": {
        "api_key": "OPENAI_O3_API_KEY",
        "api_base": "OPENAI_O3_ENDPOINT",
        "api_version": "OPENAI_O3_API_VERSION",
        "deployment_name": "OPENAI_O3_DEPLOYMENT_NAME",
        "provider": "openai"
    },
    "gemini/gemini-2.0-flash": {
        "api_key": "GEMINI_API_KEY",
        "provider": "gemini"
    }
}

def get_model_config(model_name: str) -> Dict[str, str]:
    """Get the configuration for a specific model."""
    if model_name not in MODEL_CONFIGS:
        # Default to the original configuration for backward compatibility
        return {
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
            "provider": "azure"
        }

    config = MODEL_CONFIGS[model_name]
    result = {
        "api_key": os.getenv(config["api_key"]),
        "provider": config["provider"]
    }

    # Add provider-specific configs
    if config["provider"] == "azure":
        result.update({
            "api_base": os.getenv(config["api_base"]),
            "api_version": os.getenv(config["api_version"])
        })
    elif config["provider"] == "openai":
        result.update({
            "api_base": os.getenv(config["api_base"]),
            "api_version": os.getenv(config["api_version"])
        })

    return result

def save_response_to_json(response: Union[Dict[str, Any], BaseModel], model_name: str, user_name: str = "Unknown") -> str:
    """Save the LLM response to a JSON file with metadata."""
    try:
        # Create llm_results directory if it doesn't exist
        os.makedirs("llm_results", exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Clean model name for filename
        clean_model_name = re.sub(r'[^\w\-_]', '_', model_name.replace('/', '_'))
        clean_user_name = re.sub(r'[^\w\-_]', '_', user_name.replace(' ', '_'))
        filename = f"llm_results/{timestamp}_{clean_model_name}_{clean_user_name}.json"

        # Determine provider from model name
        if "azure" in model_name:
            provider = "Azure OpenAI"
        elif "openai" in model_name:
            provider = "OpenAI"
        elif "gemini" in model_name:
            provider = "Google Gemini"
        else:
            provider = "Unknown"

        # Convert Pydantic model to dict if needed
        if hasattr(response, 'model_dump'):
            response_data = response.model_dump()
        elif hasattr(response, 'dict'):
            response_data = response.dict()
        else:
            response_data = response

        # Create the final JSON structure
        json_data = {
            "timestamp": datetime.now().isoformat(),
            "user_name": user_name,
            "model_name": clean_model_name.replace('_', '/'),
            "provider": provider,
            "result": response_data
        }

        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"💾 Response saved to: {filename}")
        return filename

    except Exception as e:
        print(f"❌ Failed to save response to JSON: {str(e)}")
        return ""

def clean_json_content(content: str) -> str:
    """Clean JSON content by removing markdown formatting and extracting valid JSON."""
    # Remove markdown code blocks
    content = re.sub(r'```json\s*\n?', '', content, flags=re.IGNORECASE)
    content = re.sub(r'```\s*\n?$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^```\s*\n?', '', content, flags=re.MULTILINE)
    content = content.replace('```', '')

    # Try to find JSON object or array
    json_match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', content, re.DOTALL)
    if json_match:
        json_content = json_match.group(0)
        # Attempt to fix incomplete JSON
        try:
            json.loads(json_content)  # Validate JSON
            return json_content.strip()
        except json.JSONDecodeError:
            # Try to fix common issues like missing closing braces
            if json_content.count('{') > json_content.count('}'):
                json_content += '}'
            if json_content.count('[') > json_content.count(']'):
                json_content += ']'
            return json_content.strip()

    # If no valid JSON found, return cleaned content as-is
    return content.strip()

def fix_gemini_json(content: str) -> str:
    """Fix common Gemini JSON formatting issues with aggressive cleaning."""
    # Remove all markdown formatting
    content = re.sub(r'```json\s*\n?', '', content, flags=re.IGNORECASE)
    content = re.sub(r'```\s*\n?', '', content, flags=re.MULTILINE)
    content = content.strip()
    
    # Find the main JSON object
    start_idx = content.find('{')
    if start_idx == -1:
        return content
    
    # Extract from first { to end
    json_part = content[start_idx:]
    
    # Fix common issues
    json_part = re.sub(r',\s*}', '}', json_part)  # Remove trailing commas before }
    json_part = re.sub(r',\s*]', ']', json_part)  # Remove trailing commas before ]
    json_part = re.sub(r'}\s*,\s*$', '}', json_part)  # Remove trailing comma at end
    
    # Fix unescaped quotes in strings - more careful approach
    json_part = re.sub(r'(?<!\\)"(?=[^"]*"[^"]*[,}\]])', '\\"', json_part)
    
    # Balance braces
    open_braces = json_part.count('{')
    close_braces = json_part.count('}')
    if open_braces > close_braces:
        json_part += '}' * (open_braces - close_braces)
    
    # Balance brackets
    open_brackets = json_part.count('[')
    close_brackets = json_part.count(']')
    if open_brackets > close_brackets:
        json_part += ']' * (open_brackets - close_brackets)
    
    return json_part.strip()

def extract_json_from_gemini_response(content: str) -> dict:
    """Extract and fix JSON from Gemini response with multiple strategies."""
    print(f"🔍 Attempting to parse Gemini response (length: {len(content)} chars)")
    print(f"📝 First 200 chars: {content[:200]}")

    strategies = [
        # Strategy 1: Direct JSON parsing after basic cleaning
        lambda c: json.loads(fix_gemini_json(c)),

        # Strategy 2: Find JSON between braces (greedy match)
        lambda c: json.loads(re.search(r'\{.*\}', c, re.DOTALL).group(0)),

        # Strategy 3: Find JSON between braces (non-greedy match)
        lambda c: json.loads(re.search(r'\{.*?\}', c, re.DOTALL).group(0)),

        # Strategy 4: Progressive brace matching
        lambda c: extract_progressive_json(c),

        # Strategy 5: Line-by-line reconstruction
        lambda c: reconstruct_json_from_lines(c),

        # Strategy 6: Extract from markdown code blocks
        lambda c: extract_json_from_markdown(c),

        # Strategy 7: Aggressive cleaning and reconstruction
        lambda c: aggressive_json_reconstruction(c),

        # Strategy 8: Field extraction with required field validation
        lambda c: extract_with_required_fields(c)
    ]

    for i, strategy in enumerate(strategies):
        try:
            result = strategy(content)
            if isinstance(result, dict) and result:
                print(f"✅ Gemini JSON extracted using strategy {i+1}")
                return result
        except Exception as e:
            print(f"❌ Gemini strategy {i+1} failed: {str(e)}")
            continue

    print(f"❌ All strategies failed. Raw content:\n{content}")
    raise json.JSONDecodeError("All JSON extraction strategies failed", content, 0)

def extract_progressive_json(content: str) -> dict:
    """Extract JSON by progressively building valid structure."""
    content = fix_gemini_json(content)
    
    # Try to find complete JSON objects
    brace_count = 0
    start_pos = content.find('{')
    if start_pos == -1:
        raise json.JSONDecodeError("No opening brace found", content, 0)
    
    for i, char in enumerate(content[start_pos:], start_pos):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                # Found complete JSON object
                json_str = content[start_pos:i+1]
                return json.loads(json_str)
    
    # If we get here, braces weren't balanced - try to fix
    json_str = content[start_pos:]
    if brace_count > 0:
        json_str += '}' * brace_count
    
    return json.loads(json_str)

def reconstruct_json_from_lines(content: str) -> dict:
    """Reconstruct JSON by parsing line by line."""
    lines = content.split('\n')
    json_lines = []
    in_json = False
    
    for line in lines:
        line = line.strip()
        if line.startswith('{') or in_json:
            in_json = True
            # Clean the line
            line = re.sub(r',\s*$', ',', line)  # Normalize trailing commas
            json_lines.append(line)
            if line.endswith('}') and line.count('}') >= line.count('{'):
                break
    
    json_str = '\n'.join(json_lines)
    json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
    json_str = re.sub(r',\s*]', ']', json_str)
    
    return json.loads(json_str)

def extract_json_from_markdown(content: str) -> dict:
    """Extract JSON from markdown code blocks."""
    # Look for JSON in markdown code blocks
    patterns = [
        r'```json\s*\n(.*?)\n```',
        r'```\s*\n(.*?)\n```',
        r'`(.*?)`'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                # Clean and try to parse
                cleaned = fix_gemini_json(match.strip())
                return json.loads(cleaned)
            except (json.JSONDecodeError, ValueError):
                continue

    # If no markdown blocks found, try the whole content
    return json.loads(fix_gemini_json(content))

def aggressive_json_reconstruction(content: str) -> dict:
    """Aggressively reconstruct JSON from partial or malformed content."""
    print("🔧 Attempting aggressive JSON reconstruction...")

    # Remove all markdown formatting
    content = re.sub(r'```[a-zA-Z]*\s*\n?', '', content, flags=re.IGNORECASE)
    content = re.sub(r'```\s*\n?', '', content, flags=re.MULTILINE)

    # Try to find the main JSON object and fix it
    start_idx = content.find('{')
    if start_idx == -1:
        raise json.JSONDecodeError("No JSON object found", content, 0)

    # Extract the JSON part
    json_content = content[start_idx:]

    # Count braces to see if we need to close the JSON
    open_braces = json_content.count('{')
    close_braces = json_content.count('}')

    print(f"🔧 Found {open_braces} opening braces, {close_braces} closing braces")

    # If JSON is incomplete, try to close it properly
    if open_braces > close_braces:
        missing_braces = open_braces - close_braces
        print(f"🔧 Adding {missing_braces} missing closing braces")

        # Find the last complete field and add closing braces
        # Look for the last complete line that ends with a quote or bracket
        lines = json_content.split('\n')
        complete_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # If line looks incomplete (ends with incomplete field name), stop here
            if line.endswith('"') and ':' not in line:
                print(f"🔧 Stopping at incomplete field: {line}")
                break

            # If line has content, add it
            if line and not line.startswith('"biomarker_pattern_analysis'):
                complete_lines.append(line)

        # Reconstruct JSON from complete lines
        reconstructed = '\n'.join(complete_lines)

        # Remove trailing comma if present
        reconstructed = re.sub(r',\s*$', '', reconstructed.strip())

        # Add missing closing braces
        reconstructed += '\n' + '}' * missing_braces

        print(f"🔧 Reconstructed JSON length: {len(reconstructed)} chars")

        try:
            return json.loads(reconstructed)
        except json.JSONDecodeError as e:
            print(f"🔧 Reconstruction failed: {str(e)}")
            # Fall back to field extraction
            pass

    # Fallback: Extract individual fields
    print("🔧 Falling back to field extraction...")
    json_parts = {}

    # Look for quoted key-value pairs
    kv_pattern = r'"([^"]+)"\s*:\s*"([^"]*)"'
    matches = re.findall(kv_pattern, content)
    for key, value in matches:
        json_parts[key] = value

    # Look for quoted key with array values
    array_pattern = r'"([^"]+)"\s*:\s*\[(.*?)\]'
    matches = re.findall(array_pattern, content, re.DOTALL)
    for key, array_content in matches:
        try:
            # Try to parse array content
            array_items = re.findall(r'"([^"]*)"', array_content)
            json_parts[key] = array_items
        except (ValueError, AttributeError):
            json_parts[key] = []

    # Look for quoted key with object values (simple objects only)
    obj_pattern = r'"([^"]+)"\s*:\s*\{([^{}]*)\}'
    matches = re.findall(obj_pattern, content)
    for key, obj_content in matches:
        try:
            # Try to parse nested object
            nested_obj = {}
            nested_matches = re.findall(kv_pattern, obj_content)
            for nested_key, nested_value in nested_matches:
                nested_obj[nested_key] = nested_value
            json_parts[key] = nested_obj
        except (ValueError, AttributeError):
            json_parts[key] = {}

    print(f"🔧 Extracted {len(json_parts)} fields: {list(json_parts.keys())[:5]}...")

    if not json_parts:
        raise json.JSONDecodeError("No JSON structure could be reconstructed", content, 0)

    return json_parts

def extract_with_required_fields(content: str) -> dict:
    """Extract JSON and ensure all required fields are present."""
    print("🔧 Attempting field extraction with required field validation...")

    # First try direct JSON parsing
    try:
        cleaned_content = fix_gemini_json(content)
        result = json.loads(cleaned_content)
        print("🔧 Direct JSON parsing successful")
    except Exception as e:
        print(f"🔧 Direct parsing failed: {e}")
        # Try to extract JSON from markdown blocks
        try:
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
                print("🔧 Markdown JSON extraction successful")
            else:
                # Try to find JSON between braces
                brace_match = re.search(r'\{.*\}', content, re.DOTALL)
                if brace_match:
                    result = json.loads(brace_match.group(0))
                    print("🔧 Brace extraction successful")
                else:
                    raise ValueError("No JSON structure found")
        except Exception as e2:
            print(f"🔧 All parsing methods failed: {e2}")
            result = {}
            print("🔧 Starting with empty result")

    # Ensure action_plan exists
    if 'action_plan' not in result:
        result['action_plan'] = {}

    action_plan = result['action_plan']

    # Add missing required fields with defaults
    if 'supplement_schedule_summary' not in action_plan:
        action_plan['supplement_schedule_summary'] = "Morning: Take supplements with breakfast. Evening: Take remaining supplements with dinner. Please consult healthcare provider for personalized timing."

    if 'supplement_disclaimer' not in action_plan:
        action_plan['supplement_disclaimer'] = "These suggestions are for educational purposes only and do not constitute medical advice. Please consult a healthcare provider before beginning any supplement regimen."

    if 'supplements' not in action_plan:
        action_plan['supplements'] = []

    if 'nutrition' not in action_plan:
        action_plan['nutrition'] = []

    if 'exercise_lifestyle' not in action_plan:
        action_plan['exercise_lifestyle'] = []

    if 'six_month_timeline' not in action_plan:
        action_plan['six_month_timeline'] = []

    # Ensure nutrition items have evidence_source
    for nutrition_item in action_plan['nutrition']:
        if isinstance(nutrition_item, dict) and 'evidence_source' not in nutrition_item:
            nutrition_item['evidence_source'] = "General nutrition guidelines from NIH and WHO recommendations"

    # Ensure exercise items have required fields
    for exercise_item in action_plan['exercise_lifestyle']:
        if isinstance(exercise_item, dict):
            if 'evidence_source' not in exercise_item:
                exercise_item['evidence_source'] = "Exercise guidelines from ACSM and WHO physical activity recommendations"
            if 'volume' not in exercise_item:
                exercise_item['volume'] = "Start with moderate volume and progress gradually"
            if 'rest_periods' not in exercise_item:
                exercise_item['rest_periods'] = "Allow adequate rest between sessions"
            if 'biomarker_connection' not in exercise_item:
                exercise_item['biomarker_connection'] = "Supports overall health and biomarker optimization"

    # Ensure other required top-level fields exist
    required_top_level = [
        'overall_health_summary',
        'congratulations_message',
        'wins_to_celebrate',
        'what_to_continue',
        'what_needs_work',
        'biomarker_snapshot',
        'goal_relevance',
        'longevity_performance_impact',
        'category_insights',
        'biomarker_insights'
    ]

    for field in required_top_level:
        if field not in result:
            if field in ['wins_to_celebrate', 'what_to_continue', 'what_needs_work', 'category_insights', 'biomarker_insights']:
                result[field] = []
            else:
                result[field] = f"Analysis for {field} could not be completed due to formatting issues."

    return result

def create_minimal_valid_response(schema: dict, raw_content: str, user_name: str) -> dict:
    """Create a minimal valid response that matches the schema when parsing fails."""
    response = {}
    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])
    
    # Fill required fields with appropriate defaults
    for field_name in required_fields:
        field_schema = properties.get(field_name, {})
        field_type = field_schema.get('type', 'string')
        
        if field_type == 'string':
            if 'summary' in field_name.lower():
                # Don't truncate - show full raw content for debugging
                response[field_name] = f"Hi {user_name}, the analysis could not be completed due to formatting issues. Raw response: {raw_content}"
            elif 'disclaimer' in field_name.lower():
                response[field_name] = f"{user_name}, these recommendations are for educational purposes only and do not constitute medical advice."
            else:
                response[field_name] = f"Unable to parse {field_name} from response"
        elif field_type == 'array':
            response[field_name] = []
        elif field_type == 'object':
            if field_name == 'action_plan':
                # Create a proper action_plan structure with required fields
                response[field_name] = {
                    'supplements': [],
                    'supplement_schedule_summary': f"Hi {user_name}, please consult with a healthcare provider for personalized supplement timing recommendations.",
                    'supplement_disclaimer': "These suggestions are for educational purposes only and do not constitute medical advice. Please consult a healthcare provider before beginning any supplement regimen.",
                    'nutrition': [],
                    'exercise_lifestyle': [],
                    'six_month_timeline': []
                }
            else:
                response[field_name] = {}
        elif field_type == 'boolean':
            response[field_name] = False
        elif field_type == 'number':
            response[field_name] = 0
    
    # Add error metadata
    response['_parsing_error'] = True
    # Don't truncate raw content - preserve full response for debugging
    response['_raw_content'] = raw_content
    response['_recommended_alternative'] = "azure/o1"
    
    return response

def create_enhanced_fallback_response(schema: dict, raw_content: str, user_name: str) -> dict:
    """Create an enhanced fallback response that extracts more content from partial responses."""
    print("🔧 Creating enhanced fallback response...")

    # Start with the minimal response
    response = create_minimal_valid_response(schema, raw_content, user_name)

    # Ensure all required fields are present with default values
    if 'action_plan' in response:
        action_plan = response['action_plan']

        # Add supplement_schedule_summary if missing
        if 'supplement_schedule_summary' not in action_plan or not action_plan['supplement_schedule_summary']:
            action_plan['supplement_schedule_summary'] = "Morning: Take supplements with breakfast. Evening: Take remaining supplements with dinner. Please consult healthcare provider for personalized timing."

        # Ensure nutrition items have evidence_source
        if 'nutrition' in action_plan:
            for nutrition_item in action_plan['nutrition']:
                if 'evidence_source' not in nutrition_item or not nutrition_item['evidence_source']:
                    nutrition_item['evidence_source'] = "General nutrition guidelines from NIH and WHO recommendations"

        # Ensure exercise items have required fields
        if 'exercise_lifestyle' in action_plan:
            for exercise_item in action_plan['exercise_lifestyle']:
                if 'evidence_source' not in exercise_item or not exercise_item['evidence_source']:
                    exercise_item['evidence_source'] = "Exercise guidelines from ACSM and WHO physical activity recommendations"
                if 'volume' not in exercise_item or not exercise_item['volume']:
                    exercise_item['volume'] = "Start with moderate volume and progress gradually"
                if 'rest_periods' not in exercise_item or not exercise_item['rest_periods']:
                    exercise_item['rest_periods'] = "Allow adequate rest between sessions"
                if 'biomarker_connection' not in exercise_item or not exercise_item['biomarker_connection']:
                    exercise_item['biomarker_connection'] = "Supports overall health and biomarker optimization"

    # Try to extract additional structured content from the raw response
    try:
        # Extract wins/celebrations if present
        wins_pattern = r'"wins_to_celebrate"\s*:\s*\[(.*?)\]'
        wins_match = re.search(wins_pattern, raw_content, re.DOTALL)
        if wins_match:
            wins_content = wins_match.group(1)
            wins = re.findall(r'"([^"]*)"', wins_content)
            if wins:
                response['wins_to_celebrate'] = wins[:3]  # Limit to 3

        # Extract what to continue if present
        continue_pattern = r'"what_to_continue"\s*:\s*\[(.*?)\]'
        continue_match = re.search(continue_pattern, raw_content, re.DOTALL)
        if continue_match:
            continue_content = continue_match.group(1)
            continue_items = re.findall(r'"([^"]*)"', continue_content)
            if continue_items:
                response['what_to_continue'] = continue_items[:3]  # Limit to 3

        # Extract what needs work if present
        work_pattern = r'"what_needs_work"\s*:\s*\[(.*?)\]'
        work_match = re.search(work_pattern, raw_content, re.DOTALL)
        if work_match:
            work_content = work_match.group(1)
            work_items = re.findall(r'"([^"]*)"', work_content)
            if work_items:
                response['what_needs_work'] = work_items[:3]  # Limit to 3

        # Extract goal relevance if present
        goal_pattern = r'"goal_relevance"\s*:\s*"([^"]*)"'
        goal_match = re.search(goal_pattern, raw_content)
        if goal_match:
            response['goal_relevance'] = goal_match.group(1)

        # Extract longevity impact if present
        longevity_pattern = r'"longevity_performance_impact"\s*:\s*"([^"]*)"'
        longevity_match = re.search(longevity_pattern, raw_content)
        if longevity_match:
            response['longevity_performance_impact'] = longevity_match.group(1)

        print(f"🔧 Enhanced fallback extracted additional fields: {len([k for k, v in response.items() if v and not k.startswith('_')])}")

    except Exception as e:
        print(f"🔧 Enhanced extraction failed: {str(e)}")

    return response

def validate_and_fix_json_fields(data: dict, schema: dict) -> dict:
    """Validate and fix JSON fields to match Pydantic schema requirements."""
    if not isinstance(data, dict):
        return data

    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])

    # Fix null values that should be strings
    def fix_null_strings(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if value is None and key in properties:
                    field_schema = properties[key]
                    if field_schema.get('type') == 'string':
                        obj[key] = "Not specified"
                elif isinstance(value, (dict, list)):
                    fix_null_strings(value)
        elif isinstance(obj, list):
            for item in obj:
                fix_null_strings(item)

    fix_null_strings(data)
    
    # Fix null values for required string fields
    for field_name, field_schema in properties.items():
        if field_name in data:
            field_type = field_schema.get('type')
            if field_type == 'string' and data[field_name] is None:
                data[field_name] = f"Not specified for {field_name}"
            elif field_type == 'array' and data[field_name] is None:
                data[field_name] = []
            elif field_type == 'object' and data[field_name] is None:
                data[field_name] = {}
        elif field_name in required_fields:
            # Add missing required fields
            field_type = field_schema.get('type', 'string')
            if field_type == 'string':
                data[field_name] = f"Not provided for {field_name}"
            elif field_type == 'array':
                data[field_name] = []
            elif field_type == 'object':
                data[field_name] = {}
            elif field_type == 'boolean':
                data[field_name] = False
    
    # Recursively fix nested objects
    for field_name, field_value in data.items():
        if isinstance(field_value, dict) and field_name in properties:
            nested_schema = properties[field_name]
            if 'properties' in nested_schema:
                data[field_name] = validate_and_fix_json_fields(field_value, nested_schema)
        elif isinstance(field_value, list) and field_name in properties:
            items_schema = properties[field_name].get('items', {})
            if 'properties' in items_schema:
                data[field_name] = [
                    validate_and_fix_json_fields(item, items_schema) if isinstance(item, dict) else item
                    for item in field_value
                ]
    
    return data

def validate_escalation_logic(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and correct escalation logic based on biomarker values.
    This ensures consistency in escalation decisions.
    """
    if not isinstance(response_data, dict):
        return response_data

    # Get biomarker insights
    biomarker_insights = response_data.get('biomarker_insights', [])

    # Check for critical biomarker values that require escalation
    escalation_needed = False
    escalation_reasons = []

    for biomarker in biomarker_insights:
        if isinstance(biomarker, dict):
            biomarker_name = biomarker.get('biomarker_name', '').lower()
            current_value = biomarker.get('current_value', '')
            status = biomarker.get('status', '')

            # Extract numeric value from current_value string
            try:
                # Handle different formats like "51.5 ml/min", "1.3 mg/dL", etc.
                numeric_value = float(''.join(filter(lambda x: x.isdigit() or x == '.', current_value.split()[0])))

                # Check critical thresholds
                if 'egfr' in biomarker_name and numeric_value < 60:
                    escalation_needed = True
                    escalation_reasons.append(f"eGFR {current_value} indicates stage-3+ kidney function; clinician review advised.")

                elif 'creatinine' in biomarker_name and numeric_value > 1.5:
                    escalation_needed = True
                    escalation_reasons.append(f"Creatinine {current_value} indicates kidney dysfunction; medical evaluation needed.")

                elif ('alt' in biomarker_name or 'ast' in biomarker_name) and numeric_value > 100:
                    escalation_needed = True
                    escalation_reasons.append(f"{biomarker_name.upper()} {current_value} indicates severe liver dysfunction; immediate medical attention required.")

                elif 'hba1c' in biomarker_name and numeric_value > 9.0:
                    escalation_needed = True
                    escalation_reasons.append(f"HbA1c {current_value} indicates uncontrolled diabetes; urgent medical review needed.")

                elif 'hemoglobin' in biomarker_name and numeric_value < 8.0:
                    escalation_needed = True
                    escalation_reasons.append(f"Hemoglobin {current_value} indicates severe anemia; medical evaluation required.")

            except (ValueError, IndexError):
                # If we can't parse the value, check status
                if status.lower() == 'red':
                    # Count red biomarkers for multiple red flag check
                    pass

    # Count red biomarkers
    red_count = sum(1 for biomarker in biomarker_insights
                   if isinstance(biomarker, dict) and biomarker.get('status', '').lower() == 'red')

    if red_count >= 3:
        escalation_needed = True
        escalation_reasons.append(f"Multiple critical biomarkers ({red_count} red flags) require comprehensive medical review.")

    # Update escalation fields if needed
    if escalation_needed:
        response_data['escalation_needed'] = True
        response_data['escalation_reason'] = escalation_reasons[0]  # Use the first/most critical reason
        print(f"🚨 Escalation triggered: {response_data['escalation_reason']}")
    else:
        response_data['escalation_needed'] = False
        response_data['escalation_reason'] = None

    return response_data

def validate_six_month_timeline(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and ensure the 6-month timeline has exactly 3 blocks.
    """
    if not isinstance(response_data, dict):
        return response_data

    action_plan = response_data.get('action_plan', {})
    if not isinstance(action_plan, dict):
        return response_data

    timeline = action_plan.get('six_month_timeline', [])

    # Check if we have exactly 3 timeline blocks
    if len(timeline) != 3:
        print(f"⚠️ Timeline validation: Found {len(timeline)} blocks, expected 3. Fixing...")

        # Create the required 3 blocks if missing
        required_blocks = [
            {
                "month_range": "Months 0-2",
                "focus_areas": ["Foundation phase: establish core habits and basic interventions"],
                "supplement_adjustments": ["Start core supplements from action plan"],
                "nutrition_focus": ["Implement basic dietary changes"],
                "exercise_goals": ["Establish consistent routine"],
                "lifestyle_targets": ["Sleep hygiene, stress management basics"],
                "retest_schedule": ["No retesting needed yet"]
            },
            {
                "month_range": "Months 3-4",
                "focus_areas": ["Optimization phase: advanced interventions and fine-tuning"],
                "supplement_adjustments": ["Add advanced supplements if needed"],
                "nutrition_focus": ["Fine-tune nutrition timing and macros"],
                "exercise_goals": ["Increase intensity or add new modalities"],
                "lifestyle_targets": ["Advanced stress management, recovery protocols"],
                "retest_schedule": ["Mid-point biomarker check if needed"]
            },
            {
                "month_range": "Months 5-6",
                "focus_areas": ["Maintenance and assessment phase: sustain changes and prepare for retest"],
                "supplement_adjustments": ["Adjust based on progress and retesting"],
                "nutrition_focus": ["Maintain optimized nutrition patterns"],
                "exercise_goals": ["Peak performance or maintenance goals"],
                "lifestyle_targets": ["Long-term habit sustainability"],
                "retest_schedule": ["Full biomarker panel retest at month 6"]
            }
        ]

        # If we have some blocks, try to preserve them and fill in missing ones
        if len(timeline) > 0:
            # Keep existing blocks and add missing ones
            for i, required_block in enumerate(required_blocks):
                if i >= len(timeline):
                    timeline.append(required_block)
                elif not timeline[i].get('month_range'):
                    timeline[i] = required_block
        else:
            # No timeline exists, create the full one
            timeline = required_blocks

        action_plan['six_month_timeline'] = timeline
        response_data['action_plan'] = action_plan
        print(f"✅ Timeline validation: Fixed to include all 3 required blocks")

    # Validate that we have the correct month ranges
    expected_ranges = ["Months 0-2", "Months 3-4", "Months 5-6"]
    actual_ranges = [block.get('month_range', '') for block in timeline]

    for i, expected_range in enumerate(expected_ranges):
        if i < len(timeline) and timeline[i].get('month_range') != expected_range:
            timeline[i]['month_range'] = expected_range
            print(f"✅ Timeline validation: Fixed month_range for block {i+1}")

    return response_data

def call_llm_with_fallback(model_name: str, messages: list, response_format: Type[BaseModel] = None, user_context=None) -> Union[Dict[str, Any], BaseModel]:
    """
    Call LLM with automatic fallback to alternative models on rate limits.

    Args:
        model_name: The primary model to use
        messages: List of message dictionaries
        response_format: Optional Pydantic model class for structured responses
        user_context: Optional user context for personalization

    Returns:
        Either a dict response or a Pydantic model instance
    """
    # Define fallback models for each provider
    fallback_models = {
        "azure/o4-mini": ["openai/o3", "gemini/gemini-2.0-flash-exp"],
        "azure/gpt-4": ["openai/o3", "gemini/gemini-2.0-flash-exp"],
        "openai/gpt-4": ["openai/o3", "gemini/gemini-2.0-flash-exp"],
        "openai/o3": ["gemini/gemini-2.0-flash-exp", "azure/o4-mini"],
        "gemini/gemini-2.0-flash-exp": ["openai/o3", "azure/o4-mini"],
        "gemini/gemini-pro": ["openai/o3", "azure/o4-mini"]
    }

    models_to_try = [model_name] + fallback_models.get(model_name, ["openai/o3", "gemini/gemini-2.0-flash-exp"])

    for i, current_model in enumerate(models_to_try):
        try:
            if i > 0:  # This is a fallback attempt
                print(f"🔄 Trying fallback model: {current_model}")

            result = call_llm(current_model, messages, response_format, user_context)

            if i > 0:  # Successfully used fallback
                print(f"✅ Successfully used fallback model: {current_model}")

            return result

        except Exception as e:
            error_str = str(e).lower()

            # Check if this is a rate limit error
            if "rate limit" in error_str or "429" in error_str or "quota" in error_str or "exceeded token rate limit" in error_str:
                if i < len(models_to_try) - 1:  # More models to try
                    print(f"⚠️ Rate limit hit for {current_model}, trying next model...")
                    continue
                else:  # No more models to try
                    raise Exception(f"Rate limit exceeded for all available models. Please try again later.")
            else:
                # Non-rate-limit error, try next model if available
                if i < len(models_to_try) - 1:
                    print(f"❌ Error with {current_model}: {str(e)}, trying next model...")
                    continue
                else:
                    # Last model failed with non-rate-limit error
                    raise e

    # Should never reach here, but just in case
    raise Exception("All models failed")

def call_llm(model_name: str, messages: list, response_format: Type[BaseModel] = None, user_context=None) -> Union[Dict[str, Any], BaseModel]:
    """
    Calls LLM (Azure OpenAI, Gemini, etc.) and returns the parsed response with enhanced personalization.
    model_name: Model name (e.g. 'azure/o1', 'azure/o4-mini', 'gemini/gemini-2.0-flash')
    messages: list of dicts (role/content)
    response_format: Optional Pydantic model class for structured output
    user_context: Optional dict with user personalization data
    """
    # Get model-specific configuration
    config = get_model_config(model_name)

    # Validate configuration for the specific model
    if not config["api_key"]:
        raise EnvironmentError(f"API key for model {model_name} must be set in environment.")

    # Azure and OpenAI models need endpoint validation
    if config["provider"] in ["azure", "openai"] and not config.get("api_base"):
        raise EnvironmentError(f"API endpoint for model {model_name} must be set in environment.")
    
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
        # Configure model-specific parameters
        # O-Series models (O1, O3, O4) only support temperature=1
        if "o_series" in model_name or "o4-mini" in model_name or "o1" in model_name or "o3" in model_name:
            temperature = 1.0
        else:
            temperature = 0.7 if user_context else 0.5  # Slightly more creative for personalized responses

        completion_params = {
            "model": model_name,
            "messages": personalized_messages,
            "temperature": temperature
        }

        # Add provider-specific parameters
        if config["provider"] == "azure":
            completion_params.update({
                "api_key": config["api_key"],
                "api_base": config["api_base"],
                "api_version": config["api_version"]
            })
            # Add max_tokens for o4-mini to ensure complete responses
            if "o4-mini" in model_name:
                completion_params["max_tokens"] = 8192  # Reduced to avoid rate limits
                # Add rate limiting parameters for Azure
                completion_params["timeout"] = 120  # Increase timeout
                completion_params["max_retries"] = 3  # Add retries
        elif config["provider"] == "openai":
            completion_params.update({
                "api_key": config["api_key"],
                "api_base": config["api_base"],
                "api_version": config["api_version"]
            })
        elif config["provider"] == "gemini":
            completion_params.update({
                "api_key": config["api_key"],
                "max_tokens": 8192  # Increase token limit for complex responses
            })

        # Add structured output format if Pydantic model is provided
        if response_format and issubclass(response_format, BaseModel):
            # Enhanced schema instruction with model-specific formatting
            schema_json = response_format.model_json_schema()
            
            if config["provider"] == "gemini":
                # Enhanced instruction for Gemini with functional medicine requirements
                schema_instruction = f"""
CRITICAL: You must respond with ONLY valid JSON. No markdown, no code blocks, no explanations.

FUNCTIONAL MEDICINE REQUIREMENTS FOR GEMINI:
- You MUST demonstrate functional medicine thinking and pattern recognition
- Identify multi-marker patterns and explain their significance
- Connect biomarkers to user's specific lifestyle, goals, and medical history
- Provide comprehensive category insights for ALL health categories
- Generate detailed biomarker insights for ALL biomarkers provided
- Include specific biomarker values and ranges in your analysis
- Reference user's actual habits, goals, and medical conditions throughout

CONTENT REQUIREMENTS:
- Generate insights for ALL categories and biomarkers provided
- Use specific biomarker values, not generic statements
- Connect patterns across multiple systems (cardiovascular + hormonal + metabolic)
- Reference user's actual lifestyle factors (training, diet, stress, medical conditions)
- Provide actionable recommendations tied to their specific situation

Schema to follow:

Required JSON Schema:
{json.dumps(schema_json, indent=2)}

CRITICAL RULES:
- All string fields must have actual string values, never null
- ALL REQUIRED FIELDS MUST BE PRESENT:
  * supplement_schedule_summary (in action_plan)
  * evidence_source (in nutrition and exercise_lifestyle items)
  * volume and rest_periods (in exercise_lifestyle items)
  * biomarker_connection (in exercise_lifestyle items)
- Generate comprehensive insights, not abbreviated ones
- Use proper JSON syntax with correct commas and brackets
- Do not include any text before or after the JSON
- Ensure all quotes are properly escaped
- Never use trailing commas
- Close all braces and brackets properly
- Provide complete functional medicine analysis in all fields
- For optional fields that don't apply, use null (not empty string)
"""
            elif "o4-mini" in model_name or "o_series" in model_name or "o3" in model_name:
                schema_instruction = f"""
You must respond with valid JSON matching this exact schema. All fields marked as required must be included with proper values (no null values for strings).

FUNCTIONAL MEDICINE REQUIREMENTS FOR O4-MINI/O-SERIES:
You MUST demonstrate functional medicine thinking and comprehensive analysis:

MANDATORY SECTIONS TO GENERATE:
- category_insights: Comprehensive insights for EACH health category with functional medicine depth
- biomarker_insights: Detailed analysis for EACH biomarker with pattern recognition
- biomarker_pattern_analysis: Multi-marker pattern identification using functional medicine principles
- action_plan: Complete personalized recommendations addressing root causes

FUNCTIONAL MEDICINE DEPTH REQUIRED:
- Identify multi-marker patterns (e.g., HPA axis dysfunction, metabolic syndrome, cardiovascular risk)
- Connect biomarkers to user's specific lifestyle, goals, and medical conditions
- Reference actual biomarker values and explain their significance
- Show systems thinking - how different body systems interact
- Provide root cause analysis, not just symptom management
- Connect patterns to user's real-life symptoms and behaviors

DO NOT leave category_insights or biomarker_insights as empty arrays. Generate comprehensive functional medicine insights for all provided data.

Schema:
{json.dumps(schema_json, indent=2)}

CRITICAL RULES:
- Every string field must contain comprehensive analysis, never null or generic content
- ALL REQUIRED FIELDS MUST BE PRESENT:
  * supplement_schedule_summary (in action_plan)
  * evidence_source (in nutrition and exercise_lifestyle items)
  * volume and rest_periods (in exercise_lifestyle items)
  * biomarker_connection (in exercise_lifestyle items)
- Reference specific biomarker values and user metadata throughout
- Demonstrate pattern recognition across multiple biomarkers
- Connect insights to user's goals, lifestyle, and medical history
- Provide complete, valid JSON only with all required fields
- Generate insights for ALL categories and biomarkers provided in the input data
- Use functional medicine principles in all analysis
- For optional fields that don't apply, use null (not empty string)
"""
            else:
                schema_instruction = f"""
Please respond with a valid JSON object that matches this exact schema:

{json.dumps(schema_json, indent=2)}

CRITICAL REQUIREMENTS:
- ALL REQUIRED FIELDS MUST BE PRESENT:
  * supplement_schedule_summary (in action_plan)
  * evidence_source (in nutrition and exercise_lifestyle items)
  * volume and rest_periods (in exercise_lifestyle items)
  * biomarker_connection (in exercise_lifestyle items)
- Ensure all required fields are included and the response is valid JSON
- Do not include any markdown formatting or code blocks - just return the raw JSON
- For optional fields that don't apply, use null (not empty string)
"""
            
            # Append schema instruction to the last user message
            if personalized_messages and personalized_messages[-1]["role"] == "user":
                personalized_messages[-1]["content"] += "\n\n" + schema_instruction
            else:
                personalized_messages.append({"role": "user", "content": schema_instruction})

            # For Azure OpenAI and OpenAI, we can use JSON mode
            if config["provider"] in ["azure", "openai"]:
                completion_params["response_format"] = {"type": "json_object"}

        response = completion(**completion_params)

        # Enhanced cost and token usage logging to terminal
        try:
            user_name = user_context.get("name", "Unknown") if user_context else "Unknown"

            # Try multiple ways to get cost information
            cost = 0.0
            if hasattr(response, '_hidden_params') and response._hidden_params:
                cost = response._hidden_params.get("response_cost", 0.0)
            elif hasattr(response, 'response_cost'):
                cost = response.response_cost
            elif 'response_cost' in response:
                cost = response['response_cost']

            # Get usage information
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            # If no usage in main response, check for it in other locations
            if not usage and hasattr(response, '_hidden_params') and response._hidden_params:
                usage = response._hidden_params.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)

            # Calculate cost if not provided (rough estimates)
            if cost == 0.0 and total_tokens > 0:
                # Rough cost estimates per 1K tokens (these are approximate)
                cost_per_1k = {
                    "azure/o1": 0.015,  # GPT-4 pricing
                    "azure/o4-mini": 0.0015,  # GPT-4 mini pricing
                    "openai/o3": 0.015,  # GPT-4 pricing
                    "gemini/gemini-2.0-flash": 0.001,  # Gemini pricing
                    "gemini/gemini-2.0-flash-exp": 0.001
                }

                base_model = model_name.lower()
                for model_key, price in cost_per_1k.items():
                    if model_key in base_model:
                        cost = (total_tokens / 1000) * price
                        break

            # Print directly to terminal (bypassing any output redirection)
            import sys
            original_stdout = sys.__stdout__
            original_stderr = sys.__stderr__

            # Temporarily restore original stdout/stderr to ensure terminal output
            sys.stdout = original_stdout
            sys.stderr = original_stderr

            print(f"💰 LLM Cost: ${cost:.6f} | Model: {model_name} | User: {user_name}")
            print(f"📊 Tokens - Input: {prompt_tokens}, Output: {completion_tokens}, Total: {total_tokens}")

            # Show cost breakdown if we have input/output token counts
            if prompt_tokens > 0 and completion_tokens > 0:
                input_cost = (prompt_tokens / 1000) * 0.001  # Rough estimate
                output_cost = (completion_tokens / 1000) * 0.002  # Rough estimate
                print(f"💵 Cost Breakdown - Input: ${input_cost:.6f}, Output: ${output_cost:.6f}")

            print("-" * 80)

            # Restore whatever stdout/stderr were set to before
            sys.stdout = sys.stdout
            sys.stderr = sys.stderr

        except Exception as e:
            # Print directly to terminal (bypassing any output redirection)
            import sys
            original_stdout = sys.__stdout__
            original_stderr = sys.__stderr__

            # Temporarily restore original stdout/stderr to ensure terminal output
            sys.stdout = original_stdout
            sys.stderr = original_stderr

            print(f"❌ Failed to log LLM cost: {str(e)}")
            print(f"🔍 Response type: {type(response)}")
            print(f"🔍 Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
            if hasattr(response, '_hidden_params'):
                print(f"🔍 Hidden params: {response._hidden_params}")

            # Try to extract any available information for debugging
            try:
                if isinstance(response, dict):
                    usage = response.get("usage", {})
                    if usage:
                        print(f"🔍 Found usage info: {usage}")

                    # Check for cost in various locations
                    for key in response.keys():
                        if 'cost' in key.lower():
                            print(f"🔍 Found cost-related key '{key}': {response[key]}")

                # Check all attributes of the response object
                if hasattr(response, '__dict__'):
                    for attr in dir(response):
                        if not attr.startswith('_') and 'cost' in attr.lower():
                            print(f"🔍 Found cost-related attribute '{attr}': {getattr(response, attr, 'N/A')}")
                        elif not attr.startswith('_') and 'usage' in attr.lower():
                            print(f"🔍 Found usage-related attribute '{attr}': {getattr(response, attr, 'N/A')}")

            except Exception as debug_e:
                print(f"🔍 Debug extraction failed: {debug_e}")

            print("-" * 80)

            # Restore whatever stdout/stderr were set to before
            sys.stdout = sys.stdout
            sys.stderr = sys.stderr

        # litellm returns a dict with 'choices', get the content from the first choice
        content = response["choices"][0]["message"]["content"]

        # Enhanced logging for debugging
        print(f"🔍 Raw LLM Response from {config['provider']}:")
        print(f"📏 Content length: {len(content)} characters")
        print(f"📝 Content preview (first 500 chars):\n{content[:500]}")
        if len(content) > 500:
            print(f"📝 Content ending (last 200 chars):\n...{content[-200:]}")
        print("-" * 80)

        # If we have a Pydantic response format, try to parse into that model
        if response_format and issubclass(response_format, BaseModel):
            try:
                # Clean the content to extract JSON
                if config["provider"] == "gemini":
                    # Use enhanced Gemini JSON extraction
                    parsed_json = extract_json_from_gemini_response(content)
                else:
                    cleaned_content = clean_json_content(content)
                    parsed_json = json.loads(cleaned_content)

                # Validate and fix JSON fields to match schema
                schema_json = response_format.model_json_schema()
                parsed_json = validate_and_fix_json_fields(parsed_json, schema_json)

                # Apply escalation validation for health reports
                if 'biomarker_insights' in parsed_json:
                    parsed_json = validate_escalation_logic(parsed_json)

                # Apply 6-month timeline validation for health reports
                if 'action_plan' in parsed_json:
                    parsed_json = validate_six_month_timeline(parsed_json)

                # Enhance parsed response with personalization markers if user context exists
                if user_context and isinstance(parsed_json, dict):
                    user_name = user_context.get('name', 'User')
                    # Add personalized disclaimer if it exists in the schema
                    if 'disclaimer' in parsed_json:
                        parsed_json['disclaimer'] = f"{user_name}, these recommendations are specifically designed with your goals in mind. These recommendations are for educational purposes only and do not constitute medical advice. Please consult a healthcare provider before starting any new regimen."

                # Create Pydantic model instance
                model_instance = response_format(**parsed_json)

                # Save to JSON file
                user_name = user_context.get('name', 'Unknown') if user_context else 'Unknown'
                save_response_to_json(model_instance, model_name, user_name)

                return model_instance

            except (json.JSONDecodeError, ValueError) as e:
                # Enhanced fallback for problematic models
                print(f"❌ JSON parsing failed: {str(e)}")
                print(f"🔍 Failed content (first 1000 chars): {content[:1000]}")
                user_name = user_context.get('name', 'User') if user_context else 'User'
                
                # Try to extract partial JSON for Gemini with more aggressive methods
                if config["provider"] == "gemini":
                    try:
                        # Try to salvage any valid JSON fragments
                        content_clean = re.sub(r'```json|```', '', content)
                        
                        # Look for any complete JSON objects in the response
                        json_objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content_clean, re.DOTALL)
                        
                        for json_obj in json_objects:
                            try:
                                # Clean and fix the JSON object
                                fixed_json = fix_gemini_json(json_obj)
                                parsed_json = json.loads(fixed_json)
                                
                                # Validate against schema
                                schema_json = response_format.model_json_schema()
                                parsed_json = validate_and_fix_json_fields(parsed_json, schema_json)
                                
                                model_instance = response_format(**parsed_json)
                                save_response_to_json(model_instance, model_name, user_name)
                                return model_instance
                            except Exception as inner_e:
                                print(f"❌ Failed to parse JSON fragment: {str(inner_e)}")
                                continue
                        
                        # If no valid JSON found, create an enhanced fallback response
                        schema_json = response_format.model_json_schema()
                        enhanced_response = create_enhanced_fallback_response(schema_json, content, user_name)
                        model_instance = response_format(**enhanced_response)
                        save_response_to_json(model_instance, model_name, user_name)
                        return model_instance
                        
                    except Exception as gemini_error:
                        print(f"❌ Gemini JSON extraction failed: {str(gemini_error)}")
                
                # For O4-mini and other models, try simpler fallback
                elif "o4-mini" in model_name:
                    try:
                        # O4-mini sometimes returns empty content
                        if not content.strip():
                            print("❌ O4-mini returned empty content")
                            schema_json = response_format.model_json_schema()
                            minimal_response = create_minimal_valid_response(schema_json, "Empty response", user_name)
                            model_instance = response_format(**minimal_response)
                            save_response_to_json(model_instance, model_name, user_name)
                            return model_instance
                        
                        # Try basic JSON cleaning
                        cleaned_content = clean_json_content(content)
                        parsed_json = json.loads(cleaned_content)
                        schema_json = response_format.model_json_schema()
                        parsed_json = validate_and_fix_json_fields(parsed_json, schema_json)
                        model_instance = response_format(**parsed_json)
                        save_response_to_json(model_instance, model_name, user_name)
                        return model_instance
                    except Exception as o4_error:
                        print(f"❌ O4-mini fallback failed: {str(o4_error)}")
                
                # Final fallback response with proper structure
                schema_json = response_format.model_json_schema()
                fallback_response = create_minimal_valid_response(schema_json, content, user_name)
                
                # Save fallback response to JSON
                save_response_to_json(fallback_response, model_name, user_name)
                return fallback_response
        else:
            # No structured format requested, try to parse as JSON or return as string
            try:
                # Clean the content to extract JSON
                if config["provider"] == "gemini":
                    cleaned_content = fix_gemini_json(content)
                else:
                    cleaned_content = clean_json_content(content)
                
                parsed_response = json.loads(cleaned_content)

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

                # Save to JSON file
                user_name = user_context.get('name', 'Unknown') if user_context else 'Unknown'
                save_response_to_json(parsed_response, model_name, user_name)

                return parsed_response

            except json.JSONDecodeError:
                # If JSON parsing fails, return as a structured response
                user_name = user_context.get('name', 'User') if user_context else 'User'
                fallback_response = {
                    "analysis_summary": f"Hi {user_name}, " + content,  # Don't truncate - show full content
                    "insights": [content],
                    "recommendations": None,
                    "disclaimer": f"{user_name}, these recommendations are for educational purposes only and do not constitute medical advice. Please consult a healthcare provider before starting any new regimen.",
                    "_personalization_applied": bool(user_context)
                }

                # Save fallback response to JSON
                save_response_to_json(fallback_response, model_name, user_name)
                return fallback_response
    except Exception as e:
        error_str = str(e).lower()

        # Handle rate limit errors specifically
        if "rate limit" in error_str or "429" in error_str or "quota" in error_str or "exceeded token rate limit" in error_str:
            error_msg = f"Rate limit exceeded for model {model_name}. Please try again in 60 seconds or switch to a different model (like openai/o3 or gemini/gemini-2.0-flash-exp)."
            print(f"❌ Rate Limit Error: {error_msg}")
            raise Exception(error_msg)

        # Handle other errors
        raise Exception(f"LLM call failed for model {model_name}: {str(e)}")