import json
import calendar
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.shortcuts import render, redirect
from .services import assign_team_for_user, get_user_ticket_balance, get_team_pool_balance,grant_initial_tickets
from apps.reservations.models import Reservation
from django.utils import timezone
from datetime import timedelta


User = get_user_model()

def _get_body(request):
    if request.content_type and request.content_type.startswith("application/json"):
        try:
            return json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
    return request.POST

@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({"ok": True})

@csrf_protect
@require_http_methods(["GET", "POST"])
def signup(request):
    if request.method == "GET":
        return render(request, "accounts/signup.html")

    data = _get_body(request)
    email = data.get("email")
    password = data.get("password")
    display_name = data.get("display_name")

    if not email or not password or not display_name:
        return JsonResponse({"error": "missing fields"}, status=400)

    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse({"error": "email already exists"}, status=400)

    try:
        with transaction.atomic():
            team = assign_team_for_user()
            user = User.objects.create_user(
                email=email,
                password=password,
                display_name=display_name,
                team=team,
            )
            grant_initial_tickets(user)
    except IntegrityError:
        return JsonResponse({"error": "email already exists"}, status=400)

    login(request, user)
    return JsonResponse({
        "id": user.id,
        "user_id": str(user.user_id),
        "email": user.email,
        "display_name": user.display_name,
        "team_id": user.team_id,
    }, status=201)

@csrf_protect
def login_view(request):
    # ✅ GET：ログイン画面を表示
    if request.method == "GET":
        return render(request, "accounts/login.html")

    # ✅ POST：JSONでログイン処理
    if request.method == "POST":
        data = _get_body(request)
        email = data.get("email")
        password = data.get("password")

        user = authenticate(request, email=email, password=password)
        if user is None:
            return JsonResponse({"error": "invalid credentials"}, status=400)

        login(request, user)
        return JsonResponse({
            "id": user.id,
            "user_id": str(user.user_id),
            "email": user.email,
            "display_name": user.display_name,
            "team_id": user.team_id,
        }, status=200)

    # 念のため
    return JsonResponse({"error": "method not allowed"}, status=405)


@csrf_protect
@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    return redirect("/auth/login/")
    


@login_required
def me(request):
    user = request.user
    team = user.team

    return JsonResponse({
        "id": user.id,
        "user_id": str(user.user_id),
        "email": user.email,
        "display_name": user.display_name,
        "team": {
            "id": team.id if team else None,
            "name": team.name if team else None,
        },
        "balances": {
            "user_tickets": get_user_ticket_balance(user),
            "team_pool": get_team_pool_balance(team) if team else 0,
        },
    })

@login_required
def mypage(request):
    user = request.user

    # 実データ
    tickets = get_user_ticket_balance(user)
    total_achievements = Reservation.objects.filter(
        user=user
    ).filter(
        Q(status="completed") | Q(completed_at__isnull=False)
    ).count()

    now = timezone.localtime()
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)

    weekly_reservations_qs = Reservation.objects.filter(
        user=user,
        start_at__gte=week_start,
        start_at__lt=week_end,
    )

    weekly_reservations = weekly_reservations_qs.count()
    weekly_achievements = weekly_reservations_qs.filter(
        Q(status="completed") | Q(completed_at__isnull=False)
    ).count()

    weekly = {
        "my_achievements": weekly_achievements,
        "my_reservations": weekly_reservations,
    }
    weekly["progress_percent"] = int(
        weekly["my_achievements"] / max(1, weekly["my_reservations"]) * 100
    )

    now = timezone.localtime()
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    weeks_in_month = (days_in_month + 6) // 7
    week_of_month = (now.day - 1) // 7 + 1
    weekly["week_label"] = f"Week {week_of_month}/{weeks_in_month}"

    reservations_qs = Reservation.objects.filter(user=user).order_by("-start_at")[:5]
    reservations = [
        {
            "date": r.start_at.strftime("%Y-%m-%d"),
            "time": r.start_at.strftime("%H:%M"),
            "status": r.status,   # scheduled / completed / missed / recovery
        }
        for r in reservations_qs
    ]

    missed = Reservation.objects.filter(
        user=user,
        status="missed",
        used_recovery=False,
    ).order_by("-start_at").first()

    recovery_available = missed is not None

    context = {
        "user": {
            "name": getattr(user, "display_name", user.email),
            "avatar": "👤",
            "tickets": tickets,
            "weekly_achievements": weekly["my_achievements"],
            "total_achievements": total_achievements,
            "recovery_available": recovery_available,
            "recovery_target_id": missed.id if missed else None,
        },
        "weekly": weekly,
        "reservations": reservations,
    }
    return render(request, "mypage.html", context)