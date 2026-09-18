from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from .forms import RegistrationForm
from .models import UserProfile


def register_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("/admin/")
        return redirect("dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():

            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )

            UserProfile.objects.create(
                user=user,
                role=form.cleaned_data["role"],
                phone=form.cleaned_data["phone"],
            )

            login(request, user)

            messages.success(
                request,
                "Your BloodLink account has been created."
            )

            if form.cleaned_data["role"] == "DONOR":
                return redirect("donor_profile")

            return redirect("dashboard")

    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


def login_view(request):

    if request.user.is_authenticated:

        if request.user.is_superuser:
            return redirect("/admin/")

        return redirect("dashboard")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:

            login(request, user)

            messages.success(
                request,
                "Welcome back to BloodLink."
            )

            if user.is_superuser:
                return redirect("/admin/")

            return redirect("dashboard")

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "accounts/login.html"
    )


def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out."
    )

    return redirect("home")


def dashboard_view(request):

    if not request.user.is_authenticated:
        return redirect("login")

    # ---------------------------------------------
    # ADMIN
    # ---------------------------------------------

    if request.user.is_superuser:
        return redirect("/admin/")

    # ---------------------------------------------
    # USER PROFILE
    # ---------------------------------------------

    try:

        profile = request.user.profile

    except UserProfile.DoesNotExist:

        logout(request)

        messages.error(
            request,
            "Your account profile was not found. Please register again."
        )

        return redirect("register")

    # Import here to avoid circular imports
    from matching.models import Match
    from notifications.models import Notification

    # ---------------------------------------------
    # DONOR DASHBOARD
    # ---------------------------------------------

    if profile.role == "DONOR":

        donor_profile = getattr(
            request.user,
            "donor_profile",
            None
        )

        if donor_profile:

            pending_matches = Match.objects.filter(
                donor=donor_profile,
                status="NOTIFIED",
            ).count()

            total_matches = Match.objects.filter(
                donor=donor_profile
            ).count()

            accepted_matches = Match.objects.filter(
                donor=donor_profile,
                status="ACCEPTED",
            ).count()

        else:

            pending_matches = 0
            total_matches = 0
            accepted_matches = 0

        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()

        return render(
            request,
            "accounts/donor_dashboard.html",
            {
                "profile": profile,
                "donor_profile": donor_profile,
                "pending_matches": pending_matches,
                "total_matches": total_matches,
                "accepted_matches": accepted_matches,
                "unread_notifications": unread_notifications,
            },
        )

    # ---------------------------------------------
    # REQUESTER DASHBOARD
    # ---------------------------------------------

    unread_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()

    blood_requests = request.user.blood_requests.all()

    total_requests = blood_requests.count()

    active_requests = blood_requests.filter(
        status__in=[
            "OPEN",
            "PARTIALLY_FULFILLED",
        ]
    ).count()

    fulfilled_requests = blood_requests.filter(
        status="FULFILLED"
    ).count()

    accepted_donors = Match.objects.filter(
        request__requester=request.user,
        status="ACCEPTED",
    ).count()

    return render(
        request,
        "accounts/requester_dashboard.html",
        {
            "profile": profile,
            "unread_notifications": unread_notifications,
            "total_requests": total_requests,
            "active_requests": active_requests,
            "fulfilled_requests": fulfilled_requests,
            "accepted_donors": accepted_donors,
        },
    )