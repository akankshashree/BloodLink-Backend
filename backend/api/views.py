from datetime import date

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from accounts.models import UserProfile
from donors.models import DonorProfile


# =========================================================
# REGISTER
# =========================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def register_api(request):

    username = request.data.get("username", "").strip()
    email = request.data.get("email", "").strip()
    phone = request.data.get("phone", "").strip()
    password = request.data.get("password", "")
    password_confirm = request.data.get("password_confirm", "")
    role = request.data.get("role", "").strip().upper()

    if not all([
        username,
        email,
        phone,
        password,
        password_confirm,
        role,
    ]):
        return Response(
            {"error": "All fields are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if password != password_confirm:
        return Response(
            {"error": "Passwords do not match."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(password) < 8:
        return Response(
            {"error": "Password must contain at least 8 characters."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if role not in ["DONOR", "REQUESTER"]:
        return Response(
            {"error": "Invalid role."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "This username is already taken."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "An account with this email already exists."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        UserProfile.objects.create(
            user=user,
            role=role,
            phone=phone,
        )

        token = Token.objects.create(user=user)

        return Response(
            {
                "message": "Account created successfully.",
                "token": token.key,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": role,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    except IntegrityError:
        return Response(
            {"error": "Unable to create account."},
            status=status.HTTP_400_BAD_REQUEST,
        )


# =========================================================
# LOGIN
# =========================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def login_api(request):

    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    if not username or not password:
        return Response(
            {"error": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(
        username=username,
        password=password,
    )

    if user is None:
        return Response(
            {"error": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token, created = Token.objects.get_or_create(user=user)

    profile = getattr(user, "profile", None)

    return Response(
        {
            "message": "Login successful.",
            "token": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": profile.role if profile else None,
            },
        }
    )


# =========================================================
# CURRENT USER
# =========================================================

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def current_user_api(request):

    user = request.user
    profile = getattr(user, "profile", None)

    return Response(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": profile.role if profile else None,
        }
    )


# =========================================================
# LOGOUT
# =========================================================

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout_api(request):

    try:
        request.user.auth_token.delete()
    except Token.DoesNotExist:
        pass

    return Response(
        {"message": "Logged out successfully."}
    )


# =========================================================
# DONOR PROFILE
# =========================================================

@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def donor_profile_api(request):

    user = request.user

    # -----------------------------------------------------
    # GET EXISTING PROFILE
    # -----------------------------------------------------

    if request.method == "GET":

        try:
            profile = user.donor_profile

        except DonorProfile.DoesNotExist:

            return Response(
                {
                    "exists": False,
                    "message": "Donor profile not created yet.",
                }
            )

        return Response(
            {
                "exists": True,
                "blood_group": profile.blood_group,
                "latitude": profile.latitude,
                "longitude": profile.longitude,
                "address": profile.address,
                "is_available": profile.is_available,
                "is_verified": profile.is_verified,
            }
        )

    # -----------------------------------------------------
    # CHECK USER ROLE
    # -----------------------------------------------------

    profile = getattr(user, "profile", None)

    if profile is None:

        return Response(
            {"error": "User profile not found."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if profile.role != "DONOR":

        return Response(
            {
                "error":
                "Only donor accounts can create donor profiles."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # -----------------------------------------------------
    # GET FORM DATA
    # -----------------------------------------------------

    blood_group = request.data.get("blood_group")
    latitude = request.data.get("latitude")
    longitude = request.data.get("longitude")
    address = request.data.get("address", "").strip()
    is_available = request.data.get("is_available", True)

    # -----------------------------------------------------
    # VALIDATE BLOOD GROUP
    # -----------------------------------------------------

    if not blood_group:

        return Response(
            {"error": "Blood group is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    valid_blood_groups = dict(
    DonorProfile.BLOOD_GROUPS
)

    if blood_group not in valid_blood_groups:

        return Response(
            {"error": "Invalid blood group."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # -----------------------------------------------------
    # VALIDATE LOCATION
    # -----------------------------------------------------

    if latitude in [None, ""] or longitude in [None, ""]:

        return Response(
            {
                "error":
                "Latitude and longitude are required."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:

        latitude = float(latitude)
        longitude = float(longitude)

    except (TypeError, ValueError):

        return Response(
            {
                "error":
                "Latitude and longitude must be valid numbers."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not -90 <= latitude <= 90:

        return Response(
            {"error": "Invalid latitude."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not -180 <= longitude <= 180:

        return Response(
            {"error": "Invalid longitude."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # -----------------------------------------------------
    # CREATE OR UPDATE DONOR PROFILE
    # -----------------------------------------------------

    donor_profile, created = DonorProfile.objects.update_or_create(
        user=user,
        defaults={
            "blood_group": blood_group,
            "latitude": latitude,
            "longitude": longitude,
            "address": address,
            "is_available": bool(is_available),
        },
    )

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return Response(
        {
            "message": (
                "Donor profile created successfully."
                if created
                else "Donor profile updated successfully."
            ),
            "profile": {
                "blood_group": donor_profile.blood_group,
                "latitude": donor_profile.latitude,
                "longitude": donor_profile.longitude,
                "address": donor_profile.address,
                "is_available": donor_profile.is_available,
                "is_verified": donor_profile.is_verified,
            },
        },
        status=(
            status.HTTP_201_CREATED
            if created
            else status.HTTP_200_OK
        ),
    )

# =========================================================
# DASHBOARD
# =========================================================

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def dashboard_api(request):

    user = request.user
    profile = getattr(user, "profile", None)

    if profile is None:
        return Response(
            {"error": "User profile not found."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from matching.models import Match
    from notifications.models import Notification

    unread_notifications = Notification.objects.filter(
        recipient=user,
        is_read=False,
    ).count()

    # -----------------------------------------------------
    # DONOR DASHBOARD
    # -----------------------------------------------------

    if profile.role == "DONOR":

        donor = getattr(user, "donor_profile", None)

        if donor:

            return Response({
                "role": "DONOR",

                "pending_matches": Match.objects.filter(
                    donor=donor,
                    status="NOTIFIED",
                ).count(),

                "total_matches": Match.objects.filter(
                    donor=donor,
                ).count(),

                "accepted_matches": Match.objects.filter(
                    donor=donor,
                    status="ACCEPTED",
                ).count(),

                "unread_notifications": unread_notifications,

                "donor_profile": {
                    "blood_group": donor.blood_group,
                    "latitude": donor.latitude,
                    "longitude": donor.longitude,
                    "address": donor.address,
                    "is_available": donor.is_available,
                    "is_verified": donor.is_verified,
                },
            })

        return Response({
            "role": "DONOR",
            "pending_matches": 0,
            "total_matches": 0,
            "accepted_matches": 0,
            "unread_notifications": unread_notifications,
            "donor_profile": None,
        })

    # -----------------------------------------------------
    # REQUESTER DASHBOARD
    # -----------------------------------------------------

    from blood_requests.models import BloodRequest

    blood_requests = BloodRequest.objects.filter(
        requester=user
    )

    return Response({

        "role": "REQUESTER",

        "total_requests": blood_requests.count(),

        "active_requests": blood_requests.filter(
            status__in=[
                "OPEN",
                "PARTIALLY_FULFILLED",
            ]
        ).count(),

        "fulfilled_requests": blood_requests.filter(
            status="FULFILLED"
        ).count(),

        "accepted_donors": Match.objects.filter(
            request__requester=user,
            status="ACCEPTED",
        ).count(),

        "unread_notifications": unread_notifications,
    })


# =========================================================
# BLOOD REQUESTS
# =========================================================

@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def blood_requests_api(request):

    from blood_requests.models import BloodRequest
    from matching.services import create_matches_for_request

    profile = getattr(request.user, "profile", None)

    if profile is None or profile.role != "REQUESTER":
        return Response(
            {
                "error":
                "Only requester accounts can manage blood requests."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # -----------------------------------------------------
    # GET REQUESTS
    # -----------------------------------------------------

    if request.method == "GET":

        requests = BloodRequest.objects.filter(
            requester=request.user
        ).order_by("-created_at")

        return Response([
            {
                "id": item.id,
                "blood_group": item.blood_group,
                "hospital_name": item.hospital_name,
                "hospital_address": item.hospital_address,
                "latitude": item.latitude,
                "longitude": item.longitude,
                "units_required": item.units_required,
                "units_fulfilled": item.units_fulfilled,
                "urgency": item.urgency,
                "radius_km": item.radius_km,
                "description": item.description,
                "status": item.status,
                "created_at": item.created_at,
                "expires_at": item.expires_at,
            }
            for item in requests
        ])

    # -----------------------------------------------------
    # CREATE REQUEST
    # -----------------------------------------------------

    required_fields = [
        "blood_group",
        "units_required",
        "urgency",
        "hospital_name",
        "hospital_address",
        "latitude",
        "longitude",
        "radius_km",
    ]

    missing = [
        field
        for field in required_fields
        if request.data.get(field) in [None, ""]
    ]

    if missing:
        return Response(
            {
                "error":
                f"Missing required fields: {', '.join(missing)}"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:

        blood_group = request.data["blood_group"]
        units_required = int(request.data["units_required"])
        latitude = float(request.data["latitude"])
        longitude = float(request.data["longitude"])
        radius_km = float(request.data["radius_km"])

    except (TypeError, ValueError):

        return Response(
            {
                "error":
                "Units, coordinates and radius must be valid numbers."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if blood_group not in dict(BloodRequest.BLOOD_GROUPS):
        return Response(
            {"error": "Invalid blood group."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    urgency = request.data["urgency"]

    if urgency not in dict(BloodRequest.URGENCY_LEVELS):
        return Response(
            {"error": "Invalid urgency level."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if units_required < 1:
        return Response(
            {"error": "At least one unit is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not -90 <= latitude <= 90:
        return Response(
            {"error": "Invalid latitude."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not -180 <= longitude <= 180:
        return Response(
            {"error": "Invalid longitude."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if radius_km <= 0:
        return Response(
            {"error": "Search radius must be greater than zero."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    blood_request = BloodRequest.objects.create(
        requester=request.user,
        blood_group=blood_group,
        hospital_name=request.data["hospital_name"].strip(),
        hospital_address=request.data["hospital_address"].strip(),
        latitude=latitude,
        longitude=longitude,
        units_required=units_required,
        urgency=urgency,
        radius_km=radius_km,
        description=request.data.get(
            "description",
            ""
        ).strip(),
    )

    # Existing matching engine
    matches = create_matches_for_request(
        blood_request
    )

    return Response(
        {
            "message":
            "Blood request created successfully.",

            "id":
            blood_request.id,

            "matches_created":
            len(matches),

            "request": {
                "id": blood_request.id,
                "blood_group": blood_request.blood_group,
                "hospital_name": blood_request.hospital_name,
                "hospital_address": blood_request.hospital_address,
                "units_required":
                    blood_request.units_required,
                "units_fulfilled":
                    blood_request.units_fulfilled,
                "urgency":
                    blood_request.urgency,
                "radius_km":
                    blood_request.radius_km,
                "description":
                    blood_request.description,
                "status":
                    blood_request.status,
                "created_at":
                    blood_request.created_at,
                "expires_at":
                    blood_request.expires_at,
            },
        },
        status=status.HTTP_201_CREATED,
    )


# =========================================================
# SINGLE BLOOD REQUEST
# =========================================================

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def blood_request_detail_api(request, request_id):

    from django.shortcuts import get_object_or_404
    from blood_requests.models import BloodRequest

    blood_request = get_object_or_404(
        BloodRequest,
        id=request_id,
    )

    if blood_request.requester != request.user:
        return Response(
            {
                "error":
                "You are not allowed to access this request."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    matches = (
        blood_request.matches
        .select_related(
            "donor",
            "donor__user",
            "donor__user__profile",
        )
        .order_by("distance_km")
    )

    serialized_matches = []

    for match in matches:

        donor_phone = None

        # Privacy:
        # phone only becomes visible after donor accepts
        if match.status == "ACCEPTED":

            donor_profile = getattr(
                match.donor.user,
                "profile",
                None,
            )

            if donor_profile:
                donor_phone = donor_profile.phone

        serialized_matches.append({

            "id": match.id,

            "request_id":
                blood_request.id,

            "status":
                match.status,

            "distance_km":
                match.distance_km,

            "donor": {
                "id":
                    match.donor.id,

                "username":
                    match.donor.user.username,

                "blood_group":
                    match.donor.blood_group,

                "address":
                    match.donor.address,
            },

            "donor_phone":
                donor_phone,
        })

    return Response({

        "request": {

            "id":
                blood_request.id,

            "blood_group":
                blood_request.blood_group,

            "hospital_name":
                blood_request.hospital_name,

            "hospital_address":
                blood_request.hospital_address,

            "latitude":
                blood_request.latitude,

            "longitude":
                blood_request.longitude,

            "units_required":
                blood_request.units_required,

            "units_fulfilled":
                blood_request.units_fulfilled,

            "urgency":
                blood_request.urgency,

            "radius_km":
                blood_request.radius_km,

            "description":
                blood_request.description,

            "status":
                blood_request.status,

            "created_at":
                blood_request.created_at,

            "expires_at":
                blood_request.expires_at,
        },

        "matches":
            serialized_matches,
    })


# =========================================================
# CANCEL BLOOD REQUEST
# =========================================================

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def cancel_blood_request_api(request, request_id):

    from django.shortcuts import get_object_or_404
    from blood_requests.models import BloodRequest

    blood_request = get_object_or_404(
        BloodRequest,
        id=request_id,
    )

    if blood_request.requester != request.user:
        return Response(
            {
                "error":
                "You are not allowed to cancel this request."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    if blood_request.status not in [
        "OPEN",
        "PARTIALLY_FULFILLED",
    ]:
        return Response(
            {
                "error":
                "This request cannot be cancelled."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    blood_request.status = "CANCELLED"

    blood_request.save(
        update_fields=["status"]
    )

    return Response({
        "message":
            "Blood request cancelled successfully.",

        "status":
            blood_request.status,
    })


# =========================================================
# DONOR MATCHES
# =========================================================

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def matches_api(request):

    from matching.models import Match

    donor = getattr(
        request.user,
        "donor_profile",
        None,
    )

    if donor is None:
        return Response(
            {
                "error":
                "Please complete your donor profile first."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    matches = (
        Match.objects
        .filter(donor=donor)
        .select_related(
            "request",
            "request__requester",
        )
        .order_by("-created_at")
    )

    return Response([

        {
            "id":
                match.id,

            "request_id":
                match.request.id,

            "status":
                match.status,

            "distance_km":
                match.distance_km,

            "request": {

                "id":
                    match.request.id,

                "blood_group":
                    match.request.blood_group,

                "hospital_name":
                    match.request.hospital_name,

                "hospital_address":
                    match.request.hospital_address,

                "units_required":
                    match.request.units_required,

                "units_fulfilled":
                    match.request.units_fulfilled,

                "urgency":
                    match.request.urgency,

                "status":
                    match.request.status,

                "created_at":
                    match.request.created_at,
            },
        }

        for match in matches
    ])


# =========================================================
# ACCEPT MATCH
# =========================================================

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def accept_match_api(request, match_id):

    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    from matching.models import Match
    from notifications.models import Notification

    donor = getattr(
        request.user,
        "donor_profile",
        None,
    )

    if donor is None:
        return Response(
            {"error": "Donor profile not found."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    match = get_object_or_404(
        Match,
        id=match_id,
        donor=donor,
    )

    if match.status != "NOTIFIED":
        return Response(
            {
                "error":
                "This match is no longer available."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    match.status = "ACCEPTED"
    match.accepted_at = timezone.now()

    match.save(
        update_fields=[
            "status",
            "accepted_at",
        ]
    )

    blood_request = match.request

    blood_request.units_fulfilled = min(
        blood_request.units_fulfilled + 1,
        blood_request.units_required,
    )

    if (
        blood_request.units_fulfilled
        >= blood_request.units_required
    ):
        blood_request.status = "FULFILLED"
    else:
        blood_request.status = "PARTIALLY_FULFILLED"

    blood_request.save(
        update_fields=[
            "units_fulfilled",
            "status",
        ]
    )

    Notification.objects.create(
        recipient=blood_request.requester,
        request=blood_request,
        notification_type="MATCH_ACCEPTED",
        title="Donor accepted your request",
        message=(
            "A matched donor has accepted "
            "your blood request."
        ),
    )

    return Response({
        "message":
            "You accepted this blood request.",

        "status":
            match.status,
    })


# =========================================================
# DECLINE MATCH
# =========================================================

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def decline_match_api(request, match_id):

    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    from matching.models import Match
    from notifications.models import Notification

    donor = getattr(
        request.user,
        "donor_profile",
        None,
    )

    if donor is None:
        return Response(
            {"error": "Donor profile not found."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    match = get_object_or_404(
        Match,
        id=match_id,
        donor=donor,
    )

    if match.status != "NOTIFIED":
        return Response(
            {
                "error":
                "This match is no longer available."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    match.status = "DECLINED"
    match.declined_at = timezone.now()

    match.save(
        update_fields=[
            "status",
            "declined_at",
        ]
    )

    Notification.objects.create(
        recipient=match.request.requester,
        request=match.request,
        notification_type="MATCH_DECLINED",
        title="Donor declined your request",
        message=(
            "A matched donor has declined "
            "your blood request."
        ),
    )

    return Response({
        "message":
            "You declined this blood request.",

        "status":
            match.status,
    })


# =========================================================
# NOTIFICATIONS
# =========================================================

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def notifications_api(request):

    from notifications.models import Notification

    notifications = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related("request")
        .order_by("-created_at")
    )

    return Response([

        {
            "id":
                item.id,

            "request_id":
                item.request_id,

            "notification_type":
                item.notification_type,

            "title":
                item.title,

            "message":
                item.message,

            "is_read":
                item.is_read,

            "created_at":
                item.created_at,
        }

        for item in notifications
    ])


# =========================================================
# MARK ONE NOTIFICATION READ
# =========================================================

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mark_notification_read_api(
    request,
    notification_id,
):

    from django.shortcuts import get_object_or_404
    from notifications.models import Notification

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user,
    )

    notification.is_read = True

    notification.save(
        update_fields=["is_read"]
    )

    return Response({
        "message":
            "Notification marked as read."
    })


# =========================================================
# MARK ALL NOTIFICATIONS READ
# =========================================================

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read_api(request):

    from notifications.models import Notification

    Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).update(
        is_read=True
    )

    return Response({
        "message":
            "All notifications marked as read."
    })


# =========================================================
# DONATION HISTORY
# =========================================================

@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def donations_api(request):

    from donors.models import DonationHistory

    donor = getattr(
        request.user,
        "donor_profile",
        None,
    )

    if donor is None:
        return Response(
            {
                "error":
                "Please complete your donor profile first."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # -----------------------------------------------------
    # GET DONATIONS
    # -----------------------------------------------------

    if request.method == "GET":

        donations = (
            DonationHistory.objects
            .filter(donor=donor)
            .order_by("-donation_date")
        )

        return Response([

            {
                "id":
                    donation.id,

                "donation_date":
                    donation.donation_date,

                "hospital_name":
                    donation.hospital_name,

                "donation_type":
                    donation.donation_type,

                "verified":
                    donation.verified,
            }

            for donation in donations
        ])

    # -----------------------------------------------------
    # ADD DONATION
    # -----------------------------------------------------

    donation_date = request.data.get(
        "donation_date"
    )

    hospital_name = request.data.get(
        "hospital_name",
        ""
    ).strip()

    donation_type = request.data.get(
        "donation_type",
        ""
    ).strip()

    if not donation_date:
        return Response(
            {"error": "Donation date is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not hospital_name:
        return Response(
            {
                "error":
                "Hospital or blood bank name is required."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not donation_type:
        return Response(
            {"error": "Donation type is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:

        donation_date = date.fromisoformat(
            donation_date
        )

    except (TypeError, ValueError):

        return Response(
            {
                "error":
                "Invalid donation date."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    donation = DonationHistory.objects.create(

        donor=donor,

        donation_date=
            donation_date,

        hospital_name=
            hospital_name,

        donation_type=
            donation_type,

        verified=False,
    )

    return Response(
        {
            "message":
                "Donation added successfully.",

            "donation": {

                "id":
                    donation.id,

                "donation_date":
                    donation.donation_date,

                "hospital_name":
                    donation.hospital_name,

                "donation_type":
                    donation.donation_type,

                "verified":
                    donation.verified,
            },
        },

        status=status.HTTP_201_CREATED,
    )