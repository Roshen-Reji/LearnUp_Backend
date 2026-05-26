"""Unified AI App Business Logic.

Supports multiple AI providers dynamically configured via the DB Settings table.
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, List

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_ROADMAP_STEPS = 4
_THINK_TAG_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

BASE_SYSTEM_PROMPT = (
    "You are LearnUp AI, the official intelligent assistant for the LearnUp platform. "
    "You help engineering students with their coursework (B.Tech, M.Tech), computer science "
    "concepts, placements, and aptitude questions. "
    "Keep answers concise, accurate, and highly encouraging. "
    "Always tailor your explanations, tone, and depth to the student's year, branch/syllabus, and learning ability."
)

APTITUDE_SCHEMA = """
Output ONLY a JSON array. Each element must follow this exact structure:
[
  {
    "text": "Question text?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "explanation": "Why this answer is correct."
  }
]
No markdown, no extra keys, no commentary — raw JSON only.
""".strip()

# ---------------------------------------------------------------------------
# Provider Clients
# ---------------------------------------------------------------------------

class BaseClient:
    def generate_chat(self, history: List[dict], system_prompt: str | None = None) -> str:
        raise NotImplementedError


class OllamaClient(BaseClient):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/") or "http://localhost:11434"
        self.model = model or "deepseek-r1:latest"

    def generate_chat(self, history: List[dict], system_prompt: str | None = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)

        payload = {"model": self.model, "messages": messages, "stream": False}
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "")
        except Exception as exc:
            logger.error(f"Ollama connection error: {exc}")
            raise Exception(f"Failed to generate response via Ollama: {exc}")


class OpenAILikeClient(BaseClient):
    def __init__(self, base_url: str, model: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.model = model or "gpt-4o"
        self.api_key = api_key

    def generate_chat(self, history: List[dict], system_prompt: str | None = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)

        payload = {"model": self.model, "messages": messages}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as exc:
            logger.error(f"OpenAI-like connection error: {exc}")
            raise Exception(f"Failed to generate response via OpenAI/Compatible API: {exc}")


class GeminiClient(BaseClient):
    def __init__(self, model: str, api_key: str):
        if not model or model.lower() == "gemini":
            self.model = "gemini-2.5-flash"
        else:
            self.model = model
        self.api_key = api_key

    def generate_chat(self, history: List[dict], system_prompt: str | None = None) -> str:
        # Gemini structure: contents array with role (user/model) and parts
        contents = []
        for msg in history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        payload = {"contents": contents}
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return ""
                return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        except Exception as exc:
            logger.error(f"Gemini connection error: {exc}")
            raise Exception(f"Failed to generate response via Gemini: {exc}")


class AnthropicClient(BaseClient):
    def __init__(self, model: str, api_key: str):
        self.model = model or "claude-3-7-sonnet-20250219"
        self.api_key = api_key

    def generate_chat(self, history: List[dict], system_prompt: str | None = None) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Anthropic doesn't allow 'system' in the messages array, it uses a top-level param
        payload = {
            "model": self.model,
            "messages": history,
            "max_tokens": 2048
        }
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data.get("content", [{}])[0].get("text", "")
        except Exception as exc:
            logger.error(f"Anthropic connection error: {exc}")
            raise Exception(f"Failed to generate response via Anthropic: {exc}")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_ai_client() -> BaseClient:
    """Read DB settings and return the appropriately configured AI client."""
    from apps.community.models import Setting
    
    settings_dict = {}
    for s in Setting.objects.all():
        settings_dict[s.key] = s.value

    provider = settings_dict.get("ai_provider", "ollama").lower()
    api_url = settings_dict.get("ai_api_url", "")
    model = settings_dict.get("ai_model", "")
    api_key = settings_dict.get("ai_api_key", "")
    
    # Fallback to env vars if DB settings are empty
    if provider == "ollama" and not api_url:
        api_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    if provider == "ollama" and not model:
        model = getattr(settings, "OLLAMA_MODEL", "deepseek-r1:latest")
    if provider == "gemini" and not api_key:
        api_key = getattr(settings, "GEMINI_API_KEY", "")

    if provider == "gemini":
        return GeminiClient(model=model, api_key=api_key)
    elif provider == "openai":
        url = api_url or "https://api.openai.com/v1"
        return OpenAILikeClient(base_url=url, model=model, api_key=api_key)
    elif provider == "anthropic":
        return AnthropicClient(model=model, api_key=api_key)
    elif provider == "groq":
        url = api_url or "https://api.groq.com/openai/v1"
        return OpenAILikeClient(base_url=url, model=model, api_key=api_key)
    elif provider == "deepseek":
        url = api_url or "https://api.deepseek.com/v1"
        return OpenAILikeClient(base_url=url, model=model, api_key=api_key)
    else:
        # Default to Ollama
        return OllamaClient(base_url=api_url, model=model)


# ---------------------------------------------------------------------------
# Helpers for response sanitisation and JSON extraction
# ---------------------------------------------------------------------------

def _strip_think_tags(text: str) -> str:
    """Remove <think>…</think> blocks emitted by reasoning models."""
    return _THINK_TAG_RE.sub("", text).strip()


def _extract_json(text: str) -> str:
    """Extract the first top‑level JSON object or array from raw LLM output."""
    text = _strip_think_tags(text).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).rstrip("`").strip()
    opener = next((c for c in text if c in ("{", "[")), None)
    if not opener:
        raise ValueError("No JSON object or array found in LLM response.")
    closer = "}" if opener == "{" else "]"
    start = text.index(opener)
    end = text.rindex(closer)
    return text[start : end + 1]


def _parse_json_response(raw: str) -> Any:
    """Parse JSON from an LLM response, raising a clear error on failure."""
    try:
        clean = _extract_json(raw)
        return json.loads(clean)
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to parse JSON from LLM response: {exc}") from exc


# ---------------------------------------------------------------------------
# Public API used by other services
# ---------------------------------------------------------------------------

def _get_student_context(user) -> str:
    """Computes and returns a rich student context string based on their profile and stats."""
    if not getattr(user, "is_authenticated", False):
        return ""
    
    points = getattr(user, "points", 0)
    streak = getattr(user, "streak_days", 0)
    
    if points > 1000 or streak > 14:
        ability = "Advanced (Capable of grasping complex engineering concepts quickly)"
    elif points > 300 or streak > 5:
        ability = "Intermediate (Has foundational knowledge, ready for deeper practical applications)"
    else:
        ability = "Beginner (Needs clear, step-by-step explanations with analogies)"
        
    return (
        f"\n\n--- STUDENT PROFILE CONTEXT ---\n"
        f"- Name: {user.name}\n"
        f"- Branch/Syllabus: {getattr(user, 'branch', 'General Engineering')}\n"
        f"- Year of Study: Year {getattr(user, 'year', 1)}\n"
        f"- Inferred Learning Ability: {ability}\n"
        "Crucial: Ensure all your explanations, examples, and depth of content are STRICTLY tailored to their syllabus, year of study, and learning ability."
    )

def process_chat_request(messages: List[dict], user=None) -> str:
    """Pass user messages to the AI service and return the assistant reply."""
    client = get_ai_client()
    system_prompt = BASE_SYSTEM_PROMPT
    if user:
        system_prompt += _get_student_context(user)
    raw = client.generate_chat(history=messages, system_prompt=system_prompt)
    return _strip_think_tags(raw)


def generate_roadmap_json(skill: str, steps: int = DEFAULT_ROADMAP_STEPS, user=None) -> List[dict]:
    """Generate a structured learning roadmap for *skill*."""
    client = get_ai_client()
    system_prompt = (
        f"Create a {steps}-step learning roadmap for: {skill}.\n"
        "Return ONLY a raw JSON array. Each element must have exactly these keys:\n"
        '  "day" (integer), "topic" (string), "details" (string)\n'
        "No markdown, no explanation, no extra keys."
    )
    if user:
        system_prompt += _get_student_context(user)
    raw = client.generate_chat([
        {"role": "user", "content": "Generate the roadmap JSON now."}
    ], system_prompt)
    parsed = _parse_json_response(raw)
    
    # Normalise fields and ensure required keys exist
    for i, node in enumerate(parsed):
        node["day"] = i + 1
        node.setdefault("details", f"Learn {node.get('topic', skill)}")
    return parsed


@dataclass
class AptitudeConfig:
    """Parameters shaping aptitude question generation."""
    topic: str
    count: int
    high_iq: bool = False
    target_branch: str = "general engineering"


def generate_aptitude_json(config: AptitudeConfig, user=None) -> List[dict]:
    """Generate *config.count* multiple‑choice aptitude questions."""
    client = get_ai_client()
    difficulty = (
        "extremely difficult and logical (High IQ level)"
        if config.high_iq
        else f"appropriate for {config.target_branch} branch students"
    )
    system_prompt = (
        f"You are an expert aptitude question generator.\n"
        f"Create exactly {config.count} multiple-choice questions about: {config.topic}.\n"
        f"Difficulty: {difficulty}.\n\n"
        f"{APTITUDE_SCHEMA}"
    )
    if user:
        system_prompt += _get_student_context(user)
    raw = client.generate_chat([
        {"role": "user", "content": "Generate the questions now."}
    ], system_prompt)
    return _parse_json_response(raw)
