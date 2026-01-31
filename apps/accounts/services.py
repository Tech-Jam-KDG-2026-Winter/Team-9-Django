from django.db import transaction
from django.db.models import Count
from .models import Teams, UserProfiles

@transaction.atomic
def assign_team_for_user():
    # 空きチームをロックして取得（人数少ない順）
    team = (
        Teams.objects
        .select_for_update()
        .filter(is_open=True)
        .annotate(member_count=Count("userprofiles"))
        .filter(member_count__lt=8)
        .order_by("member_count", "id")
        .first()
    )

    if team is None:
        team = Teams.objects.create(name="Team")  # 仮名
        team.name = f"Team-{team.id:04d}"
        team.save(update_fields=["name"])
        return team

    # 8人目で閉じる
    if team.member_count + 1 >= 8:
        team.is_open = False
        team.save(update_fields=["is_open"])

    return team
