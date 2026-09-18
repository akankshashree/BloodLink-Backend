from django.contrib.auth.models import User
from django.db import models

from blood_requests.models import BloodRequest


class Notification(models.Model):

    NOTIFICATION_TYPES = [
        ("BLOOD_REQUEST", "Blood Request"),
        ("MATCH_ACCEPTED", "Match Accepted"),
        ("MATCH_DECLINED", "Match Declined"),
        ("REQUEST_UPDATE", "Request Update"),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    request = models.ForeignKey(
        BloodRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES
    )

    title = models.CharField(
        max_length=255
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.recipient.username} | "
            f"{self.title}"
        )