from django.contrib import admin

from .models import DonorProfile, DonationHistory


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "blood_group",
        "is_available",
        "is_verified",
        "created_at",
    )

    list_filter = (
        "blood_group",
        "is_available",
        "is_verified",
    )

    search_fields = (
        "user__username",
        "user__email",
    )


@admin.register(DonationHistory)
class DonationHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "donor",
        "donation_date",
        "hospital_name",
        "donation_type",
        "verified",
    )

    list_filter = (
        "donation_type",
        "verified",
    )

    search_fields = (
        "donor__user__username",
        "hospital_name",
    )