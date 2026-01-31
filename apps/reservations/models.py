from django.conf import settings
from django.db import models

class Reservation(models.Model):

  STATUS_CHOICES = [
    ("scheduled", "予約済"),
    ("completed", "達成"),
    ("missed", "未達成"),
    ("recovery", "リカバリ"),
  ]

  ACTIVITY_CHOICES = [
    ("walk", "歩く"),
    ("run", "走る"),
    ("workout", "筋トレ"),
    ("other", "その他"),
  ]

  user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name="reservations",
  )

  team = models.ForeignKey(
    "accounts.Teams",
    on_delete=models.CASCADE,
    related_name="reservations",
    null=True,
    blank=True,
  )

  start_at = models.DateTimeField()
  status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="scheduled")
  checkin_at = models.DateTimeField(null=True, blank=True)
  completed_at = models.DateTimeField(null=True, blank=True)
  activity_type = models.CharField(max_length=16, choices=ACTIVITY_CHOICES, null=True, blank=True)
  memo = models.TextField(blank=True, default="")
  share_detail = models.BooleanField(default=False)
  used_recovery = models.BooleanField(default=False)

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f"{self.user} - {self.start_at}"