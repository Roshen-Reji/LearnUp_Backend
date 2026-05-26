"""AI App Business Logic."""

from services.ai_client import (
    process_chat_request,
    generate_roadmap_json,
    generate_aptitude_json,
    AptitudeConfig
)
import logging

logger = logging.getLogger(__name__)

# Expose functions directly from ai_client for backwards compatibility
__all__ = [
    'process_chat_request',
    'generate_roadmap_json',
    'generate_aptitude_json',
    'AptitudeConfig'
]

# We need to adapt the signature of generate_aptitude_json which was previously:
# generate_aptitude_json(topic, count, is_high_iq, target_branch)
def generate_aptitude_json_compat(topic, count, is_high_iq, target_branch, user=None):
    config = AptitudeConfig(
        topic=topic,
        count=count,
        high_iq=is_high_iq,
        target_branch=target_branch
    )
    return generate_aptitude_json(config, user=user)
