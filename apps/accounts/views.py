import json
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from .services import assign_team_for_user, get_user_ticket_balance, get_team_pool_balance

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
@require_POST
def signup(request):
    data = _get_body(request)
    email = data.get("email")
    password = data.get("password")
    display_name = data.get("display_name")

    if not email or not password or not display_name:
        return JsonResponse({"error": "missing fields"}, status=400)

    # 先に重複チェック（大文字小文字の差も吸収）
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
@require_POST
def login_view(request):
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

@csrf_protect
@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"ok": True})

@login_required
def me(request):
    user = request.user
    team = user.team

    return JsonResponse({
        "user_id": user.id,
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