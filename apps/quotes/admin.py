from django.contrib import admin
from .models import Quote


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("text", "author", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("text", "author")
