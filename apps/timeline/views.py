from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import TimelinePost, Like

@login_required
def timeline_list(request):
    return redirect("dashboard")


@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(TimelinePost, id=post_id)

    if post.user_id == request.user.id:
        return redirect("dashboard")

    like = Like.objects.filter(user=request.user, post=post).first()
    if like:
        like.delete()
    else:
        Like.objects.create(user=request.user, post=post)

    return redirect("dashboard")
