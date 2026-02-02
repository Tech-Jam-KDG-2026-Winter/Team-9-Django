from django.conf import settings
from django.db import models
from django.conf import settings

class TimelinePost(models.Model):
    VISIBILITY_CHOICES = [
        ("summary_only", "概要のみ"),
        ("with_detail", "詳細あり"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="timeline_posts",
    )

    team = models.ForeignKey(
        "accounts.Teams",
        on_delete=models.CASCADE,
        related_name="timeline_posts",
    )

    reservation = models.OneToOneField(
        "reservations.Reservation",
        on_delete=models.CASCADE,
        related_name="timeline_post",
    )

    visibility = models.CharField(max_length=16, choices=VISIBILITY_CHOICES, default="summary_only")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    post = models.ForeignKey(
        "timeline.TimelinePost",
        on_delete=models.CASCADE,
        related_name="likes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="uniq_like_user_post")
        ]
