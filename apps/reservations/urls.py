from django.urls import path
from . import views

urlpatterns = [
  path("new/", views.new_reservation, name="reservation_new"),#予約画面へ
  path("<int:reservation_id>/checkin/", views.checkin_reservation, name="reservation_checkin"),#チェックイン
  path("<int:reservation_id>/action/", views.action_reservation, name="reservation_action"),#タイマー、運動中
  path("<int:reservation_id>/complete/", views.complete_reservation, name="reservation_complete"),#記録入力、完了
  path("<int:reservation_id>/recovery/",views.use_recovery,name="reservation_recovery"),#

]