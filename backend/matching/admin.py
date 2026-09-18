from django.contrib import admin

from .models import Match


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "request",
        "donor",
        "distance_km",
        "status",
        "created_at",
        "accepted_at",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "donor__user__username",
        "request__hospital_name",
    )