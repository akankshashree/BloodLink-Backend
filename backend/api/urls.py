from django.urls import path

from .views import (
    register_api,
    login_api,
    current_user_api,
    logout_api,
    donor_profile_api,
)


urlpatterns = [

    path(
        "register/",
        register_api,
        name="api_register"
    ),

    path(
        "login/",
        login_api,
        name="api_login"
    ),

    path(
        "me/",
        current_user_api,
        name="api_me"
    ),

    path(
        "logout/",
        logout_api,
        name="api_logout"
    ),

    path(
        "donor-profile/",
        donor_profile_api,
        name="api_donor_profile"
    ),

]