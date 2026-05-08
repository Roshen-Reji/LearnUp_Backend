"""Roadmap logic."""

from .models import Roadmap, UserProgress
from django.shortcuts import get_object_or_404
from apps.accounts.services import award_points

def toggle_node(user, roadmap_id, node_index):
    """Mark a node as completed/incomplete for a user."""
    roadmap = get_object_or_404(Roadmap, id=roadmap_id)
    progress, _ = UserProgress.objects.get_or_create(user=user, roadmap=roadmap)
    
    nodes = progress.completed_nodes
    if node_index in nodes:
        nodes.remove(node_index)
        action = "removed"
    else:
        nodes.append(node_index)
        action = "added"
        # Award points for completing a node
        award_points(user, "roadmap_node_complete")
        
    progress.completed_nodes = nodes
    progress.save(update_fields=["completed_nodes", "last_accessed"])
    
    return {"status": "success", "action": action, "completed_nodes": nodes}
