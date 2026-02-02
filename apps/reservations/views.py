from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from .forms import ReservationForm
from .models import Reservation

from apps.accounts.models import TicketTransaction, TicketSource, UserProfiles
from apps.timeline.models import TimelinePost, Like
from django.db.models import Count


def can_checkin(reservation):
    now = timezone.now()
    start = reservation.start_at
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


@login_required
def dashboard(request):
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

    team = getattr(request.user, "team", None)

    timeline_posts = []
    liked_post_ids = set()

    if team:
        timeline_posts = (
            TimelinePost.objects
            .filter(team=team)
            .select_related("reservation", "user")
            .annotate(like_count=Count("likes"))
            .order_by("-created_at")[:20]
        )

        liked_post_ids = set(
            Like.objects
            .filter(user=request.user, post__team=team)
            .values_list("post_id", flat=True)
        )

    return render(request, "dashboard.html", {
        "reservation_items": reservation_items,
        "timeline_posts": timeline_posts,
        "team": team,
        "liked_post_ids": liked_post_ids,
    })



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

    if request.method != "POST":
        return redirect("dashboard")

    if reservation.checkin_at is None:
        return redirect("dashboard")

    reservation.status = "completed"
    reservation.completed_at = timezone.now()
    reservation.save(update_fields=["status", "completed_at", "updated_at"])

    return redirect("dashboard")
