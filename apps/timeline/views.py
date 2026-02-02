from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

@login_required
def timeline_list(request):
    return redirect("dashboard")