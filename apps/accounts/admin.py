from django.contrib import admin
from .models import User, UserBadge, PointEvent

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "role", "branch", "points", "ieee_status")
    search_fields = ("email", "name")
    list_filter = ("role", "branch", "ieee_status")

admin.site.register(UserBadge)
admin.site.register(PointEvent)
