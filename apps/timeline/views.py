from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import TimelinePost, Like
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from apps.accounts.models import TicketTransaction  # チームプールの計算に必要

@login_required
def timeline_list(request):
    team = getattr(request.user, "team", None)
    today = timezone.localdate()
    
    # 初期値
    team_pool_balance = 0
    today_income = 0
    today_outcome = 0

    if team:
        # 1. 現在のプール総額
        pool_data = TicketTransaction.objects.filter(
            team=team, 
            owner_type="TEAM"
        ).aggregate(total=Sum('amount'))
        team_pool_balance = pool_data['total'] or 0

        # 2. 本日の流入（未達成による没収など：amountが正の数）
        income_data = TicketTransaction.objects.filter(
            team=team,
            owner_type="TEAM",
            created_at__date=today,
            amount__gt=0
        ).aggregate(total=Sum('amount'))
        today_income = income_data['total'] or 0

        # 3. 本日の支出（amountが負の数。表示上は正の数にするために abs() か -1を掛ける）
        outcome_data = TicketTransaction.objects.filter(
            team=team,
            owner_type="TEAM",
            created_at__date=today,
            amount__lt=0
        ).aggregate(total=Sum('amount'))
        today_outcome = abs(outcome_data['total'] or 0)

        # 投稿一覧
        posts = TimelinePost.objects.filter(
            team=team
        ).select_related('user', 'reservation').annotate(
            calculated_count=Count('likes')
        ).order_by('-created_at')[:20]
    else:
        posts = []

    user_liked_post_ids = Like.objects.filter(user=request.user).values_list('post_id', flat=True)

    return render(request, "timeline/timeline_list.html", {
        "posts": posts,
        "team": team,
        "team_pool_balance": team_pool_balance,
        "today_income": today_income,
        "today_outcome": today_outcome,
        "user_liked_post_ids": list(user_liked_post_ids),
    })

@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(TimelinePost, id=post_id)
    
    if post.user_id == request.user.id:
        return JsonResponse({"error": "自分の投稿にはいいねできません"}, status=400)

    like = Like.objects.filter(user=request.user, post=post).first()
    if like:
        like.delete()
        liked = False
    else:
        Like.objects.get_or_create(user=request.user, post=post)
        liked = True

    # ★ 修正ポイント：モデルにフィールドがないので、リレーションから数える
    current_count = post.likes.count()

    return JsonResponse({"liked": liked, "count": current_count})