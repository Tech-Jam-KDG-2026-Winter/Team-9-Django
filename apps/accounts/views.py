import json
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie

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
        user = User.objects.create_user(
            email=email,
            password=password,
            display_name=display_name,
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
