from django.db import models

from blood_requests.models import BloodRequest
from donors.models import DonorProfile


class Match(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("NOTIFIED", "Notified"),
        ("ACCEPTED", "Accepted"),
        ("DECLINED", "Declined"),
        ("EXPIRED", "Expired"),
    ]

    request = models.ForeignKey(
        BloodRequest,
        on_delete=models.CASCADE,
        related_name="matches"
    )

    donor = models.ForeignKey(
        DonorProfile,
        on_delete=models.CASCADE,
        related_name="matches"
    )

    distance_km = models.FloatField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    notified_at = models.DateTimeField(
        null=True,
        blank=True
    )

    accepted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    declined_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["request", "donor"],
                name="unique_request_donor_match"
            )
        ]

    def __str__(self):
        return (
            f"{self.donor.user.username} → "
            f"{self.request.blood_group} → "
            f"{self.status}"
        )