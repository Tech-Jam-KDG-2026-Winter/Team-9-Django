from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import TimelinePost, Like

@login_required
def timeline_list(request):
    # 同じチームの投稿を新着順に取得
    # select_relatedを使うことでDBへのアクセス回数を減らして高速化します
    posts = TimelinePost.objects.filter(
        user__team=request.user.team
    ).select_related('user', 'reservation').order_by('-created_at')
    
    # 自分がどの投稿にいいねしているかのリスト（ハートの色を変える用）
    user_liked_post_ids = Like.objects.filter(user=request.user).values_list('post_id', flat=True)

    return render(request, "timeline/timeline_list.html", {
        "posts": posts,
        "user_liked_post_ids": user_liked_post_ids,
    })


@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(TimelinePost, id=post_id)

    # 自分の投稿にはいいねできない（この仕様を維持する場合）
    if post.user_id == request.user.id:
        return redirect("timeline_list")

    like = Like.objects.filter(user=request.user, post=post).first()
    if like:
        like.delete()
    else:
        Like.objects.create(user=request.user, post=post)

    # タイムラインから押されたらタイムラインに、他からならそこに戻る
    return redirect(request.META.get('HTTP_REFERER', 'timeline_list'))