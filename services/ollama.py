"""AI App Business Logic."""

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
    "Keep answers concise, accurate, and encouraging."
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
# Ollama client
# ---------------------------------------------------------------------------

class OllamaClient:
    """Thin wrapper around a local Ollama instance.

    The client is deliberately simple – it only needs to send a chat request
    and return the raw model response. All higher‑level parsing and sanitising
    happens in the helper functions below.
    """

    def __init__(self):
        self.base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = getattr(settings, "OLLAMA_MODEL", "gemma3")

    def generate_chat(self, history: List[dict], system_prompt: str | None = None) -> str:
        """Send a chat completion request to the local Ollama instance.

        Parameters
        ----------
        history: List[dict]
            List of message dicts with ``role`` and ``content`` keys.
        system_prompt: str | None
            Optional system prompt that is prepended to the conversation.
        """
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
        except httpx.RequestError as exc:
            logger.error("Ollama connection error: %s", exc)
            return f"Error: Unable to connect to local AI service ({exc})"
        except Exception as exc:
            logger.exception("Unexpected error while calling Ollama")
            return f"An internal error occurred: {exc}"

# Instantiate a singleton for importers to use
ollama = OllamaClient()

# ---------------------------------------------------------------------------
# Helpers for response sanitisation and JSON extraction
# ---------------------------------------------------------------------------

def _strip_think_tags(text: str) -> str:
    """Remove <think>…</think> blocks emitted by reasoning models."""
    return _THINK_TAG_RE.sub("", text).strip()


def _extract_json(text: str) -> str:
    """Extract the first top‑level JSON object or array from raw LLM output.

    Handles markdown fences, leading prose and stray <think> tags.
    """
    text = _strip_think_tags(text).strip()
    if text.startswith("```"):
        # Remove optional language specifier after the opening fence
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

def process_chat_request(messages: List[dict], user) -> str:
    """Pass user messages to the AI service and return the assistant reply.

    Authenticated users receive a personalised system prompt.
    """
    system_prompt = BASE_SYSTEM_PROMPT
    if getattr(user, "is_authenticated", False):
        system_prompt += (
            f"\nThe student you are talking to is {user.name}, "
            f"studying {user.branch} in year {user.year}."
        )
    raw = ollama.generate_chat(history=messages, system_prompt=system_prompt)
    return _strip_think_tags(raw)


def generate_roadmap_json(skill: str, steps: int = DEFAULT_ROADMAP_STEPS) -> List[dict]:
    """Generate a structured learning roadmap for *skill*.

    Returns a list of step dicts with ``day``, ``topic`` and ``details`` keys.
    """
    system_prompt = (
        f"Create a {steps}-step learning roadmap for: {skill}.\n"
        "Return ONLY a raw JSON array. Each element must have exactly these keys:\n"
        '  "day" (integer), "topic" (string), "details" (string)\n'
        "No markdown, no explanation, no extra keys."
    )
    raw = ollama.generate_chat([
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


def generate_aptitude_json(config: AptitudeConfig) -> List[dict]:
    """Generate *config.count* multiple‑choice aptitude questions.

    Returns a list of question dicts matching ``APTITUDE_SCHEMA``.
    """
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
    raw = ollama.generate_chat([
        {"role": "user", "content": "Generate the questions now."}
    ], system_prompt)
    return _parse_json_response(raw)