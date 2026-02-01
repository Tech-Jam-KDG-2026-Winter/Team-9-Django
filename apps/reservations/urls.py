from django.urls import path
from . import views

urlpatterns = [
  path("new/", views.new_reservation, name="reservation_new"),
  path("<int:reservation_id>/checkin/", views.checkin_reservation, name="reservation_checkin"),
  path("<int:reservation_id>/action/", views.action_reservation, name="reservation_action"),
]