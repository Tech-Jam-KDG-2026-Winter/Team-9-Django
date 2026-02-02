from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ReservationForm, ReservationCompleteForm
from .models import Reservation

from apps.accounts.models import TicketTransaction, TicketSource, UserProfiles
from apps.timeline.models import TimelinePost, Like
from django.db.models import Count


def can_checkin(reservation):
    now = timezone.now()
    start = reservation.start_at

    if timezone.is_naive(start):
        start = timezone.make_aware(start, timezone.get_current_timezone())

    return (start - timedelta(minutes=10)) <= now <= (start + timedelta(minutes=30))


# NOTE: TicketTransaction連携は Backend(1) 実装確定後に有効化予定
def _create_ticket_tx_safe(*, owner_type, user, team, source, amount, ref_type, ref_id):

    TicketTransaction.objects.get_or_create(
        owner_type=owner_type,
        user=user,
        team=team,
        source=source,
        ref_type=ref_type,
        ref_id=ref_id,
        defaults={"amount": amount},
    )


def mark_missed_reservations(user):
    now = timezone.now()
    deadline = now - timedelta(minutes=30)

    qs = Reservation.objects.filter(
        user=user,
        status="scheduled",
        completed_at__isnull=True,
        start_at__lt=deadline,
    )

    for r in qs:
        r.status = "missed"
        r.save(update_fields=["status", "updated_at"])

        _create_ticket_tx_safe(
            owner_type=TicketTransaction.OwnerType.USER,
            user=user,
            team=None,
            source=TicketSource.FAIL_TO_TEAM_POOL,
            amount=-1,
            ref_type="reservation_miss_user",
            ref_id=str(r.id),
        )

        #if getattr(user, "team", None):
            #_create_ticket_tx_safe(
               # owner_type=TicketTransaction.OwnerType.TEAM,
                #user=None,
                #team=user.team,
                #source=TicketSource.FAIL_TO_TEAM_POOL,
                #amount=1,
                #ref_type="reservation_miss_team",
                #ref_id=str(r.id),
            #)



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
    mark_missed_reservations(request.user)

    reservations = Reservation.objects.filter(
        user=request.user,
        start_at__date=timezone.localdate(),
    ).order_by("start_at")

    reservation_items = []
    for r in reservations:
        reservation_items.append({
            "reservation": r,
            "completed": (r.status == "completed") or (r.completed_at is not None),
            "checked_in": r.checkin_at is not None,
            "can_checkin": can_checkin(r) and (r.checkin_at is None),
            "missed": r.status == "missed",
            "recovery": r.status == "recovery",
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

            create_timeline_post_if_needed(r)

            return redirect("timeline_list")


            #_create_ticket_tx_safe(
                #owner_type=TicketTransaction.OwnerType.USER,
               # user=request.user,
               # team=None,
                #source=TicketSource.DEPOSIT_RETURN,  
               # amount=2,
                #ref_type="reservation_complete_user",
               # ref_id=str(reservation.id),
            #)

            #return redirect("dashboard")
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

    user = request.user

    if user.last_recovery_at:
        one_week_ago = timezone.now() - timedelta(days=7)
        if user.last_recovery_at > one_week_ago:
            return redirect("dashboard")

    reservation.status = "recovery"
    reservation.used_recovery = True
    reservation.save(update_fields=["status", "used_recovery", "updated_at"])

    _create_ticket_tx_safe(
        owner_type=TicketTransaction.OwnerType.USER,
        user=user,
        team=None,
        source=TicketSource.DEPOSIT_RETURN,
        amount=1,
        ref_type="reservation_recovery_user",
        ref_id=str(reservation.id),
    )

    if getattr(user, "team", None):
        _create_ticket_tx_safe(
            owner_type=TicketTransaction.OwnerType.TEAM,
            user=None,
            team=user.team,
            source=TicketSource.DEPOSIT_RETURN,
            amount=-1,
            ref_type="reservation_recovery_team",
            ref_id=str(reservation.id),
        )

    user.last_recovery_at = timezone.now()
    user.save(update_fields=["last_recovery_at"])

    return redirect("dashboard")


def create_timeline_post_if_needed(reservation):
    if hasattr(reservation, "timeline_post"):
        return reservation.timeline_post


    team = getattr(reservation.user, "team", None)
    if team is None:
        return None

    if reservation.team_id != team.id:
        reservation.team = team
        reservation.save(update_fields=["team", "updated_at"])

    visibility = "with_detail" if reservation.share_detail else "summary_only"

    return TimelinePost.objects.create(
        user=reservation.user,
        team=team,
        reservation=reservation,
        visibility=visibility,
    )
