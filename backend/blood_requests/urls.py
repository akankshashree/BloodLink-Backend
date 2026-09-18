from django.urls import path

from .views import (
    create_blood_request,
    blood_request_detail,
    my_blood_requests,
)


urlpatterns = [

    path(
        "create/",
        create_blood_request,
        name="create_blood_request",
    ),

    path(
        "my/",
        my_blood_requests,
        name="my_blood_requests",
    ),

    path(
        "<int:request_id>/",
        blood_request_detail,
        name="blood_request_detail",
    ),
]