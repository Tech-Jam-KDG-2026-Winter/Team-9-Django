from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ReservationForm


@login_required
def new_reservation(request):
    if request.method == "POST":
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.save()
            return redirect("dashboard")
    else:
        form = ReservationForm()

    return render(request, "reservations/new.html", {"form": form})


def dashboard(request):
    return render(request, "dashboard.html")