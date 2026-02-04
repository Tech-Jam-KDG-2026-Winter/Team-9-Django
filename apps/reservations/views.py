from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ReservationForm, ReservationCompleteForm
from .models import Reservation
from apps.timeline.models import TimelinePost, Like
from apps.accounts.services import (
    create_reservation_deposit,
    create_deposit_return,
    create_admin_bonus,
    create_fail_to_team_pool,
    create_recovery,
)


# =========================
# 共通ロジック
# =========================

def can_checkin(reservation):
    now = timezone.now()
    start = reservation.start_at

    if timezone.is_naive(start):
        start = timezone.make_aware(start, timezone.get_current_timezone())

    return (start - timedelta(minutes=10)) <= now <= (start + timedelta(minutes=30))


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

        if getattr(user, "team", None):
            create_fail_to_team_pool(user.team, r.id)


# =========================
# 予約作成
# =========================

@login_required
def new_reservation(request):
    if request.method == "POST":
        form = ReservationForm(request.POST, user=request.user)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.team = getattr(request.user, "team", None)
            reservation.save()

            create_reservation_deposit(request.user, reservation.id)
            return redirect("dashboard")
    else:
        form = ReservationForm(user=request.user)

    return render(request, "reservations/new.html", {"form": form})


# =========================
# ダッシュボード
# =========================

@login_required
def dashboard(request):
    #期限切れ予約のチェック（ステータス更新）
    mark_missed_reservations(request.user)

    now = timezone.now()
    team = getattr(request.user, "team", None)

    last = request.user.last_recovery_at
    today = timezone.localdate()
    cooldown_ok = not (last and last > (now - timedelta(days=7)))

    # --- 追加・修正：月曜リセットロジック ---
    # 今週の月曜日 0:00 を取得
    start_of_week = today - timedelta(days=today.weekday())
    
    last = request.user.last_recovery_at
    cooldown_ok = True
    if last:
        # 最後にリカバリーした日が「今週の月曜日」以降なら、今週はもう使えない
        if last.date() >= start_of_week:
            cooldown_ok = False

    # リカバリーが使用可能か判定
    recovery_available = bool(team) and cooldown_ok
    # --- ここまで ---

    # 今日以降の予約を取得（__date__gte=today で明日以降も含む）
    reservations = (
        Reservation.objects.filter(
            user=request.user,
            start_at__date__gte=today,
        )
        .order_by("start_at")
    )

    reservation_items = []
    for r in reservations:
        # 予約が今日かどうか
        local_start = timezone.localtime(r.start_at)
        is_today = local_start.date() == today
        
        # ステータスが書き換わっていなくても、時間が30分以上過ぎていたらmissed扱いとして扱う（表示用）
        is_missed = r.status == "missed"
        if r.status == "scheduled" and r.start_at + timedelta(minutes=30) < now:
            is_missed = True

        reservation_items.append({
            "reservation": r,
            "is_today": is_today,
            "completed": (r.status == "completed") or (r.completed_at is not None),
            "checked_in": r.checkin_at is not None,
            "can_checkin": can_checkin(r) and (r.checkin_at is None),
            "missed": is_missed,
            "recovery": r.status == "recovery",
            "recovery_available": recovery_available,  
        })

    # 4. チームのタイムライン取得
    team = getattr(request.user, "team", None)
    timeline_posts = []
    liked_post_ids = set()

    if team:
        timeline_posts = (
            TimelinePost.objects
            .filter(team=team)
            .select_related("reservation", "user")
            .annotate(calculated_count=Count("likes"))
            .order_by("-created_at")[:20]
        )

        liked_post_ids = set(
            Like.objects
            .filter(user=request.user, post__team=team)
            .values_list("post_id", flat=True)
        )

    return render(
        request,
        "dashboard.html",
        {
            "reservation_items": reservation_items,
            "timeline_posts": timeline_posts,
            "team": team,
            "liked_post_ids": liked_post_ids,
            "today": today,
        },
    )


# =========================
# チェックイン
# =========================

@require_POST
@login_required
def checkin_reservation(request, reservation_id):
    reservation = get_object_or_404(
        Reservation,
        id=reservation_id,
        user=request.user,
    )

    if not can_checkin(reservation):
        return redirect("/?error=checkin_time")

    if reservation.checkin_at is None:
        reservation.checkin_at = timezone.now()
        reservation.save(update_fields=["checkin_at", "updated_at"])

    return redirect("reservation_action", reservation_id=reservation.id)


@login_required
def action_reservation(request, reservation_id):
    reservation = get_object_or_404(
        Reservation,
        id=reservation_id,
        user=request.user,
    )

    if reservation.checkin_at is None:
        return redirect("/?error=need_checkin")

    return render(
        request,
        "reservations/action.html",
        {"reservation": reservation},
    )


# =========================
# 完了処理
# =========================

@login_required
def complete_reservation(request, reservation_id):
    reservation = get_object_or_404(
        Reservation,
        id=reservation_id,
        user=request.user,
    )

    if reservation.status == "completed" or reservation.completed_at is not None:
        return redirect("timeline_list")

    if reservation.checkin_at is None:
        return redirect("/?error=need_checkin")
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    if request.method == "POST":
        form = ReservationCompleteForm(request.POST, instance=reservation)
        if form.is_valid():
            r = form.save(commit=False)
            r.status = "completed"
            r.completed_at = timezone.now()
            r.save(update_fields=[
                "activity_type",
                "memo",
                "share_detail",
                "status",
                "completed_at",
                "updated_at",
            ])

            create_deposit_return(request.user, r.id)
            create_admin_bonus(request.user, r.id)

            create_timeline_post_if_needed(r)

            return redirect("timeline_list")
    else:
        form = ReservationCompleteForm(instance=reservation)

    return render(request, "reservations/record.html", {
        "reservation": reservation,
        "form": form,
    })


# =========================
# リカバリー
# =========================

@require_POST
@login_required
def use_recovery(request, reservation_id):
    reservation = get_object_or_404(
        Reservation,
        id=reservation_id,
        user=request.user,
    )

    if reservation.status != "missed":
        return redirect("dashboard")

    if reservation.used_recovery:
        return redirect("dashboard")

    user = request.user
    team = getattr(user, "team", None)

    if team is None:
        return redirect("/?error=no_team")

    # --- 追加・修正：月曜リセットロジックに変更 ---
    today = timezone.localdate()
    start_of_week = today - timedelta(days=today.weekday())

    if user.last_recovery_at:
        if user.last_recovery_at.date() >= start_of_week:
            # 今週すでに使用済み
            return redirect("/?error=recovery_cooldown")
    # --- ここまで ---

    reservation.status = "recovery"
    reservation.used_recovery = True
    reservation.save(update_fields=["status", "used_recovery", "updated_at"])

    create_recovery(user, team, ref_id=reservation.id)

    user.last_recovery_at = timezone.now()
    user.save(update_fields=["last_recovery_at"])

    return redirect("dashboard")


# =========================
# タイムライン投稿
# =========================

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
