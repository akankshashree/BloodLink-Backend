from math import asin, cos, radians, sin, sqrt
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from donors.models import DonorProfile
from notifications.models import Notification

from .constants import (
    DEFAULT_MATCH_RADIUS_KM,
    MIN_DONATION_INTERVAL_DAYS,
)
from .models import Match


def calculate_distance_km(
    latitude1,
    longitude1,
    latitude2,
    longitude2,
):
    """
    Calculate approximate distance between two
    latitude/longitude coordinates using Haversine formula.
    """

    earth_radius_km = 6371.0

    lat1 = radians(latitude1)
    lat2 = radians(latitude2)

    delta_lat = radians(latitude2 - latitude1)
    delta_lon = radians(longitude2 - longitude1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * asin(sqrt(a))

    return earth_radius_km * c


def get_last_donation(donor):
    """
    Return the donor's most recent recorded donation.
    """

    return donor.donations.order_by(
        "-donation_date"
    ).first()


def donation_interval_eligible(donor):
    """
    Check whether the donor has completed the configured
    minimum donation interval.
    """

    last_donation = get_last_donation(donor)

    if last_donation is None:
        return True, "No previous donation recorded."

    earliest_next_date = (
        last_donation.donation_date
        + timedelta(days=MIN_DONATION_INTERVAL_DAYS)
    )

    today = timezone.localdate()

    if today >= earliest_next_date:
        return (
            True,
            "Required donation interval has passed.",
        )

    days_remaining = (
        earliest_next_date - today
    ).days

    return (
        False,
        f"Donation interval not complete. "
        f"{days_remaining} day(s) remaining.",
    )


def blood_group_compatible(
    donor_blood_group,
    requested_blood_group,
):
    """
    Prototype red-cell donor compatibility matrix.
    """

    compatibility = {
        "O-": {
            "O-",
            "O+",
            "A-",
            "A+",
            "B-",
            "B+",
            "AB-",
            "AB+",
        },

        "O+": {
            "O+",
            "A+",
            "B+",
            "AB+",
        },

        "A-": {
            "A-",
            "A+",
            "AB-",
            "AB+",
        },

        "A+": {
            "A+",
            "AB+",
        },

        "B-": {
            "B-",
            "B+",
            "AB-",
            "AB+",
        },

        "B+": {
            "B+",
            "AB+",
        },

        "AB-": {
            "AB-",
            "AB+",
        },

        "AB+": {
            "AB+",
        },
    }

    return requested_blood_group in compatibility.get(
        donor_blood_group,
        set(),
    )


def check_donor_eligibility(
    donor,
    requested_blood_group=None,
):
    """
    Perform all donor-level eligibility checks.

    Verification is NOT required for matching in the prototype.
    """

    reasons = []

    # Donor must currently be available.
    if not donor.is_available:
        reasons.append(
            "Donor is currently unavailable."
        )

    # Check minimum donation interval.
    interval_ok, interval_reason = (
        donation_interval_eligible(donor)
    )

    if not interval_ok:
        reasons.append(interval_reason)

    # Check blood group compatibility.
    if requested_blood_group is not None:

        compatible = blood_group_compatible(
            donor.blood_group,
            requested_blood_group,
        )

        if not compatible:
            reasons.append(
                "Blood group is not compatible."
            )

    return {
        "eligible": len(reasons) == 0,
        "reasons": reasons,
    }


def find_eligible_donors(
    blood_request,
    radius_km=None,
):
    """
    Find donors satisfying:

    - availability
    - donation interval
    - blood compatibility
    - geographical radius

    Verification is intentionally NOT required
    for the current prototype.

    Results are sorted by distance.
    """

    if radius_km is None:
        radius_km = (
            blood_request.radius_km
            or DEFAULT_MATCH_RADIUS_KM
        )

    # IMPORTANT:
    # is_verified is NOT required here.
    donors = DonorProfile.objects.select_related(
        "user"
    ).filter(
        is_available=True,
    )

    eligible_donors = []

    for donor in donors:

        eligibility = check_donor_eligibility(
            donor,
            blood_request.blood_group,
        )

        if not eligibility["eligible"]:
            continue

        distance = calculate_distance_km(
            donor.latitude,
            donor.longitude,
            blood_request.latitude,
            blood_request.longitude,
        )

        if distance > radius_km:
            continue

        eligible_donors.append(
            {
                "donor": donor,
                "distance_km": round(
                    distance,
                    2,
                ),
            }
        )

    eligible_donors.sort(
        key=lambda item: item["distance_km"]
    )

    return eligible_donors


@transaction.atomic
def create_matches_for_request(blood_request):
    """
    Find eligible donors and create Match records.

    Existing matches are not duplicated.

    Newly created matches are marked as NOTIFIED and
    an in-app notification is created for each donor.
    """

    if blood_request.status not in [
        "OPEN",
        "PARTIALLY_FULFILLED",
    ]:
        return []

    eligible_donors = find_eligible_donors(
        blood_request
    )

    matches = []

    for item in eligible_donors:

        donor = item["donor"]
        distance = item["distance_km"]

        match, created = Match.objects.get_or_create(
            request=blood_request,
            donor=donor,
            defaults={
                "distance_km": distance,
                "status": "NOTIFIED",
                "notified_at": timezone.now(),
            },
        )

        if created:

            Notification.objects.create(
                recipient=donor.user,
                request=blood_request,
                notification_type="BLOOD_REQUEST",
                title="Nearby blood request",
                message=(
                    f"A {blood_request.blood_group} blood "
                    f"request has been created at "
                    f"{blood_request.hospital_name}, "
                    f"approximately {distance} km away."
                ),
            )

        else:

            match.distance_km = distance
            match.save(
                update_fields=["distance_km"]
            )

        matches.append(match)

    return matches