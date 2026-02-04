from datetime import timedelta
from django import forms
from django.utils import timezone

from .models import Reservation


class ReservationForm(forms.ModelForm):
    # HTML上で表示する「年」を含まない選択肢
    date = forms.ChoiceField(
        label="日付", 
        widget=forms.Select(attrs={'class': 'form-input-field'})
    )
    # スマホでドラムロールになる時間選択
    time = forms.TimeField(
        label="時間", 
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-input-field'})
    )

    class Meta:
        model = Reservation
        # start_atは手動で合成するためfieldsからは除外する
        fields = []

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # 「今日」と「明日」の選択肢を生成
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)
        self.fields['date'].choices = [
            (today.isoformat(), "今日"),
            (tomorrow.isoformat(), "明日")
        ]

    def clean(self):
        cleaned_data = super().clean()
        date_str = cleaned_data.get("date")
        time_obj = cleaned_data.get("time")
        user = self.user

        if not date_str or not time_obj:
            return cleaned_data

        # 日付と時間を合成してawareなdatetimeオブジェクトを作る
        # start_at = 2026-02-03 17:00:00 的な形
        start_at_str = f"{date_str} {time_obj}"
        start_at = timezone.make_aware(
            timezone.datetime.strptime(start_at_str, "%Y-%m-%d %H:%M:%S"),
            timezone.get_current_timezone()
        )


        # 現在時刻（日本時間）
        now = timezone.now()

        # --- 過去時刻のチェック ---
        # 余裕を持って「今から5分後」より前ならエラーにする
        if start_at < (now + timedelta(minutes=1)):
            raise forms.ValidationError("現在より前の時刻で予約を入れることはできません。")

        # 1日2枠まで
        day = timezone.localdate(start_at)
        day_count = Reservation.objects.filter(
            user=user,
            start_at__date=day,
        ).count()

        if day_count >= 2:
            raise forms.ValidationError("予約は1日2枠までです。")

        # 前後3時間空ける
        lower = start_at - timedelta(hours=3)
        upper = start_at + timedelta(hours=3)

        conflict_exists = Reservation.objects.filter(
            user=user,
            start_at__gt=lower,
            start_at__lt=upper,
        ).exists()

        if conflict_exists:
            raise forms.ValidationError("予約は前後3時間以上空けてください。")

        # 合成した値をcleaned_dataにセット
        cleaned_data["start_at"] = start_at
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # cleanメソッドで作成したstart_atをモデルに代入
        instance.start_at = self.cleaned_data["start_at"]
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance


class ReservationCompleteForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["activity_type", "memo", "share_detail"]
        widgets = {
            'activity_type': forms.Select(attrs={'class': 'form-input-field'}),
            'memo': forms.Textarea(attrs={
                'class': 'form-input-field',
                'rows': 3,
                'placeholder': '運動の感想など（任意）'
            }),
            'share_detail': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean_activity_type(self):
        v = self.cleaned_data.get("activity_type")
        if not v:
            raise forms.ValidationError("種別を選んでください")
        return v