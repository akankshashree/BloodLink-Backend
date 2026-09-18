from django.urls import path

from .views import (
    accept_match_view,
    decline_match_view,
    donor_matches_view,
)


urlpatterns = [
    path("donor/", donor_matches_view, name="donor_matches"),
    path("<int:match_id>/accept/", accept_match_view, name="accept_match"),
    path("<int:match_id>/decline/", decline_match_view, name="decline_match"),
]