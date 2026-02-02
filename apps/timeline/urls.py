from django.urls import path
from . import views
urlpatterns = [
    path("", views.timeline_list, name="timeline_list"),
    path("<int:post_id>/like/", views.toggle_like, name="timeline_like"),
]
