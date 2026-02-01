from django import forms
from .models import Reservation


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["start_at"]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"})
        }