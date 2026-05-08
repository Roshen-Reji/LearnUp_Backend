"""Placements Business Logic."""

from .models import Placement

def log_custom_placement(user_name, user_id, validated_data):
    """Fallback manual entry by user if needed."""
    return Placement.objects.create(
        posted_by=user_name,
        user_id=user_id,
        **validated_data
    )

def clear_and_sync_placements(placements_data):
    """
    Called by a scraper/bot (system) to refresh the board.
    Wipes the current list, saves all new.
    """
    Placement.objects.all().delete()
    
    placement_objects = []
    for data in placements_data:
        placement_objects.append(
            Placement(
                company=data.get('company', 'Unknown'),
                role=data.get('role', 'SDE'),
                salary=data.get('salary', 'Not disclosed'),
                batch=data.get('batch', '2025/2026'),
                link=data.get('link', ''),
                requirements=data.get('requirements', []),
                posted_by="SystemScraper"
            )
        )
        
    Placement.objects.bulk_create(placement_objects)
    return len(placement_objects)
