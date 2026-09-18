def check_donor_eligibility(
    donor,
    requested_blood_group=None,
):
    """
    Perform all donor-level eligibility checks.
    """

    reasons = []

    if not donor.is_available:
        reasons.append(
            "Donor is currently unavailable."
        )

    interval_ok, interval_reason = (
        donation_interval_eligible(donor)
    )

    if not interval_ok:
        reasons.append(interval_reason)

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

    Results are sorted by distance.
    """

    if radius_km is None:
        radius_km = (
            blood_request.radius_km
            or DEFAULT_MATCH_RADIUS_KM
        )

    donors = DonorProfile.objects.select_related(
        "user"
    ).filter(
        is_available=True,
    )