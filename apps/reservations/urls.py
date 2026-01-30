from django.urls import path
from . import views

urlpatterns = [
  path("new/", views.new_reservation, name="reservation_new"),
]