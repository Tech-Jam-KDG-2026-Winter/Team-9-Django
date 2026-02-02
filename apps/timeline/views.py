from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect,get_object_or_404
from .models import TimelinePost, Like
from apps.accounts.models import UserProfiles

@login_required
def timeline_list(request):
    return redirect("dashboard")

@login_required
def toggle_like(request, post_id):
    if request.method != "POST":
        return redirect("dashboard")

    post = get_object_or_404(TimelinePost, id=post_id)


    profile = UserProfiles.objects.select_related("team").filter(user_id=request.user.id).first()
    if not profile or not profile.team or post.team_id != profile.team_id:
        return redirect("dashboard")

    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()

    return redirect("dashboard")
