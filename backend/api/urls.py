from django.urls import path

from .views import (
    register_api,
    login_api,
    current_user_api,
    logout_api,
    donor_profile_api,

    dashboard_api,

    blood_requests_api,
    blood_request_detail_api,
    cancel_blood_request_api,

    matches_api,
    accept_match_api,
    decline_match_api,

    notifications_api,
    mark_notification_read_api,
    mark_all_notifications_read_api,

    donations_api,
)


urlpatterns = [

    # Authentication
    path(
        "register/",
        register_api,
        name="api_register",
    ),

    path(
        "login/",
        login_api,
        name="api_login",
    ),

    path(
        "me/",
        current_user_api,
        name="api_me",
    ),

    path(
        "logout/",
        logout_api,
        name="api_logout",
    ),


    # Donor profile
    path(
        "donor-profile/",
        donor_profile_api,
        name="api_donor_profile",
    ),


    # Dashboard
    path(
        "dashboard/",
        dashboard_api,
        name="api_dashboard",
    ),


    # Blood requests
    path(
        "blood-requests/",
        blood_requests_api,
        name="api_blood_requests",
    ),

    path(
        "blood-requests/<int:request_id>/",
        blood_request_detail_api,
        name="api_blood_request_detail",
    ),

    path(
        "blood-requests/<int:request_id>/cancel/",
        cancel_blood_request_api,
        name="api_cancel_blood_request",
    ),


    # Matches
    path(
        "matches/",
        matches_api,
        name="api_matches",
    ),

    path(
        "matches/<int:match_id>/accept/",
        accept_match_api,
        name="api_accept_match",
    ),

    path(
        "matches/<int:match_id>/decline/",
        decline_match_api,
        name="api_decline_match",
    ),


    # Notifications
    path(
        "notifications/",
        notifications_api,
        name="api_notifications",
    ),

    path(
        "notifications/<int:notification_id>/read/",
        mark_notification_read_api,
        name="api_notification_read",
    ),

    path(
        "notifications/read-all/",
        mark_all_notifications_read_api,
        name="api_notifications_read_all",
    ),


    # Donation history
    path(
        "donations/",
        donations_api,
        name="api_donations",
    ),
]