from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification


@login_required
def notification_list_view(request):
    """
    Display notifications belonging only to the logged-in user.
    """

    notifications = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related("request")
        .order_by("-created_at")
    )

    return render(
        request,
        "notifications/list.html",
        {
            "notifications": notifications,
        },
    )


@login_required
def mark_notification_read_view(request, notification_id):
    """
    Mark one notification as read.

    The notification must belong to the currently logged-in user.
    """

    if request.method != "POST":
        return redirect("notification_list")

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user,
    )

    notification.is_read = True

    notification.save(
        update_fields=["is_read"]
    )

    return redirect("notification_list")


@login_required
def mark_all_notifications_read_view(request):
    """
    Mark all notifications belonging to the logged-in user as read.
    """

    if request.method != "POST":
        return redirect("notification_list")

    Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).update(
        is_read=True
    )

    messages.success(
        request,
        "All notifications marked as read."
    )

    return redirect("notification_list")