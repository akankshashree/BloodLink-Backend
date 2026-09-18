from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import DonorProfileForm, DonationHistoryForm
from .models import DonorProfile, DonationHistory


@login_required
def donor_profile_view(request):

    if not hasattr(request.user, "profile"):
        messages.error(
            request,
            "Your account profile was not found."
        )
        return redirect("login")

    if request.user.profile.role != "DONOR":
        messages.error(
            request,
            "Only donors can access this page."
        )
        return redirect("dashboard")

    donor_profile = getattr(
        request.user,
        "donor_profile",
        None
    )

    if request.method == "POST":

        form = DonorProfileForm(
            request.POST,
            instance=donor_profile
        )

        if form.is_valid():

            donor = form.save(commit=False)
            donor.user = request.user
            donor.save()

            messages.success(
                request,
                "Your donor profile has been saved successfully."
            )

            return redirect("donor_profile")

    else:

        form = DonorProfileForm(
            instance=donor_profile
        )

    return render(
        request,
        "donors/profile.html",
        {
            "form": form,
            "donor_profile": donor_profile,
        },
    )


@login_required
def donation_history_view(request):

    if not hasattr(request.user, "profile"):
        return redirect("login")

    if request.user.profile.role != "DONOR":
        messages.error(
            request,
            "Only donors can access this page."
        )
        return redirect("dashboard")

    donor_profile = getattr(
        request.user,
        "donor_profile",
        None
    )

    if donor_profile is None:
        messages.warning(
            request,
            "Please complete your donor profile first."
        )
        return redirect("donor_profile")

    if request.method == "POST":

        form = DonationHistoryForm(request.POST)

        if form.is_valid():

            donation = form.save(commit=False)
            donation.donor = donor_profile
            donation.save()

            messages.success(
                request,
                "Donation history added successfully."
            )

            return redirect("donation_history")

    else:

        form = DonationHistoryForm()

    donations = DonationHistory.objects.filter(
        donor=donor_profile
    ).order_by("-donation_date")

    return render(
        request,
        "donors/donation_history.html",
        {
            "form": form,
            "donations": donations,
        },
    )