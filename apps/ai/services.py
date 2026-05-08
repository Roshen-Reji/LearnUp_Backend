"""AI App Business Logic."""

from services.ollama import ollama
import json
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are LearnUp AI, the official intelligent assistant for the LearnUp platform. 
You help engineering students with their coursework (B.Tech, M.Tech), computer science concepts, 
placements, and aptitude questions. Keep answers concise, accurate, and encouraging."""

def process_chat_request(messages, user):
    """Passes user messages to the centralized AI service."""
    
    # We could theoretically prepend context about the user
    # e.g. "The user is a {user.branch} year {user.year} student."
    
    context_prompt = SYSTEM_PROMPT
    if user.is_authenticated:
        context_prompt += f"\nThe user you are talking to is named {user.name}, studying {user.branch} in year {user.year}."
        
    response_text = ollama.generate_chat(
        history=messages,
        system_prompt=context_prompt
    )
    
    # Strip <think> blocks so the AI chat UI isn't polluted with reasoning logs
    import re
    response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
    
    return response_text

import re

def _clean_json_response(response_text):
    """Helper method to extract JSON reliably from LLM text responses."""
    clean_json = response_text.strip()
    
    # Remove deepseek-r1 <think> tags and their contents
    clean_json = re.sub(r'<think>.*?</think>', '', clean_json, flags=re.DOTALL).strip()
    
    # Attempt to strictly match the first valid JSON array or object
    start_idx = -1
    for i, c in enumerate(clean_json):
        if c in ('[', '{'):
            start_idx = i
            break
            
    if start_idx != -1:
        end_char = ']' if clean_json[start_idx] == '[' else '}'
        end_idx = clean_json.rfind(end_char)
        if end_idx != -1:
            clean_json = clean_json[start_idx:end_idx+1]
            
    return clean_json.strip()

def generate_roadmap_json(skill):
    """Generates a structured learning roadmap for a specific skill via AI."""
    sys_prompt = f"Create a learning roadmap for {skill} in exactly 4 steps. Return raw JSON array of objects with 'day', 'topic', 'details'. Nothing else."
    
    try:
        resp = ollama.generate_chat([{"role": "user", "content": "Make JSON."}], sys_prompt)
        clean_json = _clean_json_response(resp)
        parsed = json.loads(clean_json)
        
        for i, node in enumerate(parsed):
            node["day"] = i + 1
            node["completed"] = False
            if "details" not in node: 
                node["details"] = "Learn " + node.get("topic", "")
        return parsed
    except Exception as e:
        logger.error(f"AI Roadmap Generation failed for {skill}: {e}")
        return None

def generate_aptitude_json(topic, count, is_high_iq, target_branch):
    """Extracts aptitude questions in bulk via AI."""
    system_prompt = f"You are an expert aptitude question generator. Create {count} multiple choice questions about {topic}."
    if is_high_iq:
        system_prompt += " Make them extremely difficult and logical (High IQ level)."
    else:
        system_prompt += f" Target them for {target_branch} branch students."
        
    system_prompt += """
    Output ONLY a JSON array of objects with this exact structure:
    [
      {
        "text": "Question text?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_index": 0,
        "explanation": "Why this is correct."
      }
    ]
    Do not add any markdown formatting, just raw JSON.
    """
    
    try:
        response = ollama.generate_chat([{"role": "user", "content": "Generate the questions now in pure JSON."}], system_prompt)
        clean_json = _clean_json_response(response)
        return json.loads(clean_json)
    except Exception as e:
        logger.error(f"AI Aptitude Generation failed for {topic}: {e}")
        return None
