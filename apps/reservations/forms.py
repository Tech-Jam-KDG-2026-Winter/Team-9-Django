from django import forms
from .models import Reservation


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["start_at"]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"})
        }

class ReservationCompleteForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["activity_type", "memo", "share_detail"]

    def clean_activity_type(self):
        v = self.cleaned_data.get("activity_type")
        if not v:
            raise forms.ValidationError("種別を選んでください")
        return v