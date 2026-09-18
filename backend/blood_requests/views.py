from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from matching.services import create_matches_for_request

from .forms import BloodRequestForm
from .models import BloodRequest


@login_required
def create_blood_request(request):

    if not hasattr(request.user, "profile"):
        messages.error(
            request,
            "Your account profile was not found."
        )
        return redirect("login")

    if request.user.profile.role != "REQUESTER":
        messages.error(
            request,
            "Only requesters can create blood requests."
        )
        return redirect("dashboard")

    if request.method == "POST":

        form = BloodRequestForm(request.POST)

        if form.is_valid():

            blood_request = form.save(commit=False)

            blood_request.requester = request.user

            blood_request.save()

            matches = create_matches_for_request(
                blood_request
            )

            if matches:

                messages.success(
                    request,
                    f"Blood request created successfully. "
                    f"{len(matches)} eligible donor(s) were matched and notified."
                )

            else:

                messages.warning(
                    request,
                    "Blood request created, but no eligible donors "
                    "were found within the selected radius."
                )

            return redirect(
                "blood_request_detail",
                request_id=blood_request.id
            )

    else:

        form = BloodRequestForm()

    return render(
        request,
        "blood_requests/create.html",
        {
            "form": form
        }
    )


@login_required
def blood_request_detail(request, request_id):

    blood_request = get_object_or_404(
        BloodRequest,
        id=request_id
    )

    # Only the requester who created the request
    # can view its donor matches.
    if blood_request.requester != request.user:

        messages.error(
            request,
            "You are not allowed to view this request."
        )

        return redirect("dashboard")

    matches = list(
        blood_request.matches
        .select_related(
            "donor",
            "donor__user",
            "donor__user__profile",
        )
        .order_by("distance_km")
    )

    # ------------------------------------------------
    # PRIVACY CONTROL
    # ------------------------------------------------
    #
    # We DO NOT expose donor contact information by
    # default.
    #
    # Phone is added to the response context ONLY when:
    #
    # 1. The requester owns this blood request
    # 2. This donor is matched to this request
    # 3. The donor has ACCEPTED the match
    #
    # Otherwise phone remains None.
    # ------------------------------------------------

    for match in matches:

        match.revealed_phone = None

        if match.status == "ACCEPTED":

            try:

                match.revealed_phone = (
                    match.donor.user.profile.phone
                )

            except Exception:

                match.revealed_phone = None

    return render(
        request,
        "blood_requests/detail.html",
        {
            "blood_request": blood_request,
            "matches": matches,
        }
    )


@login_required
def my_blood_requests(request):

    requests = (
        BloodRequest.objects
        .filter(requester=request.user)
        .order_by("-created_at")
    )

    return render(
        request,
        "blood_requests/my_requests.html",
        {
            "requests": requests
        }
    )