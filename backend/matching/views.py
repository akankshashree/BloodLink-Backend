from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from notifications.models import Notification

from .models import Match


@login_required
def donor_matches_view(request):
    """
    Show all blood requests matched with the logged-in donor.
    """

    if not hasattr(request.user, "profile"):
        messages.error(request, "Your account profile was not found.")
        return redirect("login")

    if request.user.profile.role != "DONOR":
        messages.error(request, "Only donors can access this page.")
        return redirect("dashboard")

    if not hasattr(request.user, "donor_profile"):
        messages.warning(
            request,
            "Please complete your donor profile first."
        )
        return redirect("donor_profile")

    donor = request.user.donor_profile

    matches = (
        Match.objects
        .filter(donor=donor)
        .select_related("request", "request__requester")
        .order_by("-created_at")
    )

    return render(
        request,
        "matching/donor_matches.html",
        {
            "matches": matches,
        },
    )


@login_required
def accept_match_view(request, match_id):
    """
    Allow the matched donor to accept a blood request.
    """

    if request.method != "POST":
        return redirect("donor_matches")

    if not hasattr(request.user, "donor_profile"):
        messages.error(
            request,
            "Donor profile not found."
        )
        return redirect("dashboard")

    donor = request.user.donor_profile

    match = get_object_or_404(
        Match,
        id=match_id,
        donor=donor,
    )

    if match.status != "NOTIFIED":
        messages.warning(
            request,
            "This match is no longer available for acceptance."
        )
        return redirect("donor_matches")

    # ---------------------------------------------
    # ACCEPT MATCH
    # ---------------------------------------------

    match.status = "ACCEPTED"
    match.accepted_at = timezone.now()

    match.save(
        update_fields=[
            "status",
            "accepted_at",
        ]
    )

    # ---------------------------------------------
    # UPDATE BLOOD REQUEST FULFILLMENT
    # ---------------------------------------------

    blood_request = match.request

    # One accepted donor = one fulfilled unit
    blood_request.units_fulfilled += 1

    # Never allow fulfilled units to exceed required units
    if blood_request.units_fulfilled >= blood_request.units_required:

        blood_request.units_fulfilled = blood_request.units_required
        blood_request.status = "FULFILLED"

    else:

        blood_request.status = "PARTIALLY_FULFILLED"

    blood_request.save(
        update_fields=[
            "units_fulfilled",
            "status",
        ]
    )

    # ---------------------------------------------
    # NOTIFY REQUESTER
    # ---------------------------------------------

    Notification.objects.create(
        recipient=match.request.requester,
        request=match.request,
        notification_type="MATCH_ACCEPTED",
        title="Donor accepted your request",
        message=(
            "A matched donor has accepted your blood request."
        ),
    )

    messages.success(
        request,
        "You accepted this blood request."
    )

    return redirect("donor_matches")


@login_required
def decline_match_view(request, match_id):
    """
    Allow the matched donor to decline a blood request.
    """

    if request.method != "POST":
        return redirect("donor_matches")

    if not hasattr(request.user, "donor_profile"):
        messages.error(
            request,
            "Donor profile not found."
        )
        return redirect("dashboard")

    donor = request.user.donor_profile

    match = get_object_or_404(
        Match,
        id=match_id,
        donor=donor,
    )

    if match.status != "NOTIFIED":
        messages.warning(
            request,
            "This match is no longer available."
        )
        return redirect("donor_matches")

    # ---------------------------------------------
    # DECLINE MATCH
    # ---------------------------------------------

    match.status = "DECLINED"
    match.declined_at = timezone.now()

    match.save(
        update_fields=[
            "status",
            "declined_at",
        ]
    )

    # ---------------------------------------------
    # NOTIFY REQUESTER
    # ---------------------------------------------

    Notification.objects.create(
        recipient=match.request.requester,
        request=match.request,
        notification_type="MATCH_DECLINED",
        title="Donor declined your request",
        message=(
            "A matched donor has declined your blood request."
        ),
    )

    messages.info(
        request,
        "You declined this blood request."
    )

    return redirect("donor_matches")