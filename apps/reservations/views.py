from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.utils import timezone
from .forms import ReservationForm, ReservationCompleteForm
from .models import Reservation


def can_checkin(reservation):
    now = timezone.now()
    start = reservation.start_at

    if timezone.is_naive(start):
        start = timezone.make_aware(start, timezone.get_current_timezone())

    return (start - timedelta(minutes=10)) <= now <= (start + timedelta(minutes=30))


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

def mark_missed_reservations(user):
    now = timezone.now()
    deadline = now - timedelta(minutes=30)

    qs = Reservation.objects.filter(
        user=user,
        status="scheduled",
        completed_at__isnull=True,
        start_at__lt=deadline,
    )

    qs.update(status="missed", updated_at=now)

def dashboard(request):
    mark_missed_reservations(request.user)

    reservations = Reservation.objects.filter(
        user=request.user,
        start_at__date=timezone.localdate(),
    )

    reservation_items = []
    for r in reservations:
        reservation_items.append({
            "reservation": r,
            "completed": r.status == "completed" or r.completed_at is not None,
            "checked_in": r.checkin_at is not None,
            "can_checkin": can_checkin(r) and r.checkin_at is None,
        })

    return render(request, "dashboard.html", {"reservation_items": reservation_items})


@login_required
def checkin_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)

    if request.method != "POST":
        return redirect("dashboard")

    if not can_checkin(reservation):
        return redirect("/?error=checkin_time")

    if reservation.checkin_at is None:
        reservation.checkin_at = timezone.now()
        reservation.save(update_fields=["checkin_at", "updated_at"])

    return redirect("reservation_action", reservation_id=reservation.id)


@login_required
def action_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)

    if reservation.checkin_at is None:
        return redirect("/?error=need_checkin")

    return render(request, "reservations/action.html", {"reservation": reservation})


@login_required
def complete_reservation(request, reservation_id):
    reservation = get_object_or_404(
        Reservation,
        id=reservation_id,
        user=request.user,
    )

    if reservation.status == "completed" or reservation.completed_at is not None:
        return redirect("dashboard")

    if reservation.checkin_at is None:
        return redirect("dashboard")

    if request.method == "POST":
        form = ReservationCompleteForm(request.POST, instance=reservation)
        if form.is_valid():
            r = form.save(commit=False)
            r.status = "completed"
            r.completed_at = timezone.now()
            r.save(update_fields=[
                "activity_type", "memo", "share_detail",
                "status", "completed_at", "updated_at"
            ])
            return redirect("dashboard")
    else:
        form = ReservationCompleteForm(instance=reservation)

    return render(
        request,
        "reservations/record.html",
        {"reservation": reservation, "form": form},
    )

@login_required
def use_recovery(request, reservation_id):
    reservation = get_object_or_404(
        Reservation,
        id=reservation_id,
        user=request.user,
    )

    if request.method != "POST":
        return redirect("dashboard")

    if reservation.status != "missed":
        return redirect("dashboard")

    if reservation.used_recovery:
        return redirect("dashboard")

    profile = request.user

    if profile.last_recovery_at:
        one_week_ago = timezone.now() - timedelta(days=7)
        if profile.last_recovery_at > one_week_ago:
            return redirect("dashboard")

    reservation.status = "recovery"
    reservation.used_recovery = True
    reservation.save(update_fields=["status", "used_recovery", "updated_at"])

    profile.last_recovery_at = timezone.now()
    profile.save(update_fields=["last_recovery_at"])

    return redirect("dashboard")