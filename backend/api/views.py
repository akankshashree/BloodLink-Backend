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
        DonorProfile.BLOOD_GROUP_CHOICES
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