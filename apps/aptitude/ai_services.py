
import json
import logging
from .models import Question

logger = logging.getLogger("apps.aptitude")

def generate_custom_questions(topic, category, count, is_high_iq, target_branch, user=None):
    """Generate generic custom questions."""
    try:
        from apps.ai.services import generate_aptitude_json_compat
        data = generate_aptitude_json_compat(topic, count, is_high_iq, target_branch, user=user)
        if not data:
            raise Exception("AI Returned No Generative JSON Data.")
        
        created = []
        for q in data:
            obj = Question.objects.create(
                text=q.get("text", "Generated Question"),
                options=q.get("options", ["A", "B", "C", "D"]),
                correct_index=q.get("correct_index", 0),
                explanation=q.get("explanation", ""),
                category="coding" if is_high_iq else category,
                difficulty="hard" if is_high_iq else "medium",
                is_high_iq=is_high_iq,
                target_branch=target_branch,
                approved=False,
                ai_generated=True
            )
            created.append({
                "id": str(obj.id),
                "text": obj.text,
                "options": obj.options
            })
            
        return created
    except Exception as e:
        logger.error(f"AI Generation failed: {e}")
        raise Exception(f"AI Generation failed: {e}")

def generate_daily_questions():
    """Generates 9 questions automatically."""
    count = 3
    generate_custom_questions("Basic Programming", "coding", count, False, "General")
    generate_custom_questions("Logical Reasoning", "numerical", count, False, "General")
    generate_custom_questions("English Grammar", "verbal", count, False, "General")
    return {"coding": count, "numerical": count, "verbal": count}
