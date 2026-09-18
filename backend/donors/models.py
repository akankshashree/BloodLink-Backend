from django.contrib.auth.models import User
from django.db import models


class DonorProfile(models.Model):

    BLOOD_GROUPS = [
        ("O+", "O+"),
        ("O-", "O-"),
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="donor_profile"
    )

    blood_group = models.CharField(
        max_length=3,
        choices=BLOOD_GROUPS
    )

    latitude = models.FloatField()

    longitude = models.FloatField()

    address = models.CharField(
        max_length=255,
        blank=True
    )

    is_available = models.BooleanField(
        default=True
    )

    is_verified = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.blood_group}"


class DonationHistory(models.Model):

    donor = models.ForeignKey(
        DonorProfile,
        on_delete=models.CASCADE,
        related_name="donations"
    )

    donation_date = models.DateField()

    hospital_name = models.CharField(
        max_length=255,
        blank=True
    )

    donation_type = models.CharField(
        max_length=50,
        default="Whole Blood"
    )

    verified = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.donor.user.username} - "
            f"{self.donation_date}"
        )