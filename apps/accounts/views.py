import json
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from .services import assign_team_for_user, get_user_ticket_balance, get_team_pool_balance,grant_initial_tickets

from django.shortcuts import render

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
    return render(request, "accounts/login.html")


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

    # 仮データ（実装時は実データに差し替え）
    weekly = {
        "my_achievements": 4,
        "my_reservations": 5,
    }
    weekly["progress_percent"] = int(weekly["my_achievements"] / max(1, weekly["my_reservations"]) * 100)

    reservations = [
        {"date": "2026-02-03", "time": "07:00", "status": "completed"},
        {"date": "2026-02-04", "time": "19:00", "status": "pending"},
    ]

    context = {
        "user": {
            "name": getattr(user, "display_name", user.email),
            "avatar": "👤",
            "tickets": 7,
            "weekly_achievements": 4,
            "total_achievements": 47,
            "recovery_available": True,
        },
        "weekly": weekly,
        "reservations": reservations,
    }
    return render(request, "mypage.html", context)