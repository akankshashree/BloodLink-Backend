from django.urls import path

from .views import (
    mark_all_notifications_read_view,
    mark_notification_read_view,
    notification_list_view,
)


urlpatterns = [

    path(
        "",
        notification_list_view,
        name="notification_list",
    ),

    path(
        "<int:notification_id>/read/",
        mark_notification_read_view,
        name="mark_notification_read",
    ),

    path(
        "mark-all-read/",
        mark_all_notifications_read_view,
        name="mark_all_notifications_read",
    ),

]