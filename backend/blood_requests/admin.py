from django.contrib import admin

from .models import BloodRequest


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "requester",
        "blood_group",
        "hospital_name",
        "units_required",
        "units_fulfilled",
        "urgency",
        "status",
        "created_at",
    )

    list_filter = (
        "blood_group",
        "urgency",
        "status",
    )

    search_fields = (
        "hospital_name",
        "requester__username",
    )