from django.urls import path

from .views import (
    donation_history_view,
    donor_profile_view,
)


urlpatterns = [
    path(
        "profile/",
        donor_profile_view,
        name="donor_profile",
    ),

    path(
        "history/",
        donation_history_view,
        name="donation_history",
    ),
]