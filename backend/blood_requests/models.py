from django.contrib.auth.models import User
from django.db import models


class BloodRequest(models.Model):

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

    URGENCY_LEVELS = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("CRITICAL", "Critical"),
    ]

    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("PARTIALLY_FULFILLED", "Partially Fulfilled"),
        ("FULFILLED", "Fulfilled"),
        ("CANCELLED", "Cancelled"),
        ("EXPIRED", "Expired"),
    ]

    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="blood_requests"
    )

    blood_group = models.CharField(
        max_length=3,
        choices=BLOOD_GROUPS
    )

    hospital_name = models.CharField(
        max_length=255
    )

    hospital_address = models.CharField(
        max_length=500
    )

    latitude = models.FloatField()

    longitude = models.FloatField()

    units_required = models.PositiveIntegerField(
        default=1
    )

    units_fulfilled = models.PositiveIntegerField(
        default=0
    )

    urgency = models.CharField(
        max_length=10,
        choices=URGENCY_LEVELS,
        default="MEDIUM"
    )

    radius_km = models.FloatField(
        default=10
    )

    description = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="OPEN"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return (
            f"{self.blood_group} | "
            f"{self.hospital_name} | "
            f"{self.status}"
        )