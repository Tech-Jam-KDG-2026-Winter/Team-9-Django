from datetime import timedelta
from django import forms
from django.utils import timezone

from .models import Reservation


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["start_at"]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"})
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user  # ★追加

    def clean_start_at(self):
        start_at = self.cleaned_data["start_at"]
        user = self.user

        if user is None:
            return start_at 

        if timezone.is_naive(start_at):
            start_at = timezone.make_aware(
                start_at,
                timezone.get_current_timezone()
            )

        # 1日2枠まで
        day = timezone.localdate(start_at)
        day_count = Reservation.objects.filter(
            user=user,
            start_at__date=day,
        ).count()

        if day_count >= 2:
            raise forms.ValidationError("予約は1日2枠までです。")

        #前後3時間空ける（日またぎも有効）
        lower = start_at - timedelta(hours=3)
        upper = start_at + timedelta(hours=3)

        conflict_exists = Reservation.objects.filter(
            user=user,
            start_at__gt=lower,
            start_at__lt=upper,
        ).exists()

        if conflict_exists:
            raise forms.ValidationError(
                "予約は前後3時間以上空けてください。"
            )

        return start_at


class ReservationCompleteForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["activity_type", "memo", "share_detail"]

    def clean_activity_type(self):
        v = self.cleaned_data.get("activity_type")
        if not v:
            raise forms.ValidationError("種別を選んでください")
        return v
