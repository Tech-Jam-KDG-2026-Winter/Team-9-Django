from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import TimelinePost, Like
from django.http import JsonResponse
from django.db.models import Count # これを追加

@login_required
def timeline_list(request):
    posts = TimelinePost.objects.filter(
        user__team=request.user.team
    ).select_related('user', 'reservation').annotate(
        # ページを開いた時のために、各投稿のいいね数を数えておく
        calculated_count=Count('likes')
    ).order_by('-created_at')
    
    user_liked_post_ids = Like.objects.filter(user=request.user).values_list('post_id', flat=True)

    return render(request, "timeline/timeline_list.html", {
        "posts": posts,
        "user_liked_post_ids": list(user_liked_post_ids), # set/list化しておくとJS判定しやすい
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