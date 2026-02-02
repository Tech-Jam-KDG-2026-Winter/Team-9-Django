from django.urls import path
from . import views
urlpatterns = [
    path("", views.timeline_list, name="timeline_list"),
]