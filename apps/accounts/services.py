from django.db import transaction
from django.db.models import Count, Sum
from .models import Teams, UserProfiles, TicketTransaction, TicketSource


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

def get_user_ticket_balance(user):
    return (
        TicketTransaction.objects
        .filter(owner_type=TicketTransaction.OwnerType.USER, user=user)
        .aggregate(total=Sum("amount"))
        .get("total") or 0
    )

def get_team_pool_balance(team):
    return (
        TicketTransaction.objects
        .filter(owner_type=TicketTransaction.OwnerType.TEAM, team=team)
        .aggregate(total=Sum("amount"))
        .get("total") or 0
    )

def grant_initial_tickets(user):
    ticket, _ = TicketTransaction.objects.get_or_create(
        owner_type=TicketTransaction.OwnerType.USER,
        user=user,
        source=TicketSource.INITIAL_GRANT,
        ref_type="initial_grant",
        ref_id=str(user.user_id),
        defaults={"amount": 7},
    )
    return ticket

# 予約時のデポジット：ユーザーチケット -1
def create_reservation_deposit(user, reservation_id):
    return TicketTransaction.objects.get_or_create(
        owner_type=TicketTransaction.OwnerType.USER,
        user=user,
        source=TicketSource.RESERVATION_DEPOSIT,
        ref_type="reservation",
        ref_id=str(reservation_id),
        defaults={"amount": -1},
    )[0]

# 達成時にデポジットのリターン：ユーザーチケット +1
def create_deposit_return(user, reservation_id):
    return TicketTransaction.objects.get_or_create(
        owner_type=TicketTransaction.OwnerType.USER,
        user=user,
        source=TicketSource.DEPOSIT_RETURN,
        ref_type="reservation",
        ref_id=str(reservation_id),
        defaults={"amount": 1},
    )[0]

# 達成時の運営ボーナス：ユーザーチケット +1
def create_admin_bonus(user, reservation_id):
    return TicketTransaction.objects.get_or_create(
        owner_type=TicketTransaction.OwnerType.USER,
        user=user,
        source=TicketSource.ADMIN_BONUS,
        ref_type="reservation",
        ref_id=str(reservation_id),
        defaults={"amount": 1},
    )[0]

# 未達時のチケット回収：チームチケット +1
def create_fail_to_team_pool(team, reservation_id):
    return TicketTransaction.objects.get_or_create(
        owner_type=TicketTransaction.OwnerType.TEAM,
        team=team,
        source=TicketSource.FAIL_TO_TEAM_POOL,
        ref_type="reservation",
        ref_id=str(reservation_id),
        defaults={"amount": 1},
    )[0]

# 週1リカバリ用：チームチケット -1, ユーザーチケット +1
def create_recovery(user, team, ref_id):
    user_tx, _ = TicketTransaction.objects.get_or_create(
        owner_type=TicketTransaction.OwnerType.USER,
        user=user,
        source=TicketSource.RECOVERY,
        ref_type="recovery",
        ref_id=str(ref_id),
        defaults={"amount": 1},
    )
    team_tx, _ = TicketTransaction.objects.get_or_create(
        owner_type=TicketTransaction.OwnerType.TEAM,
        team=team,
        source=TicketSource.RECOVERY,
        ref_type="recovery",
        ref_id=str(ref_id),
        defaults={"amount": -1},
    )
    return user_tx, team_tx