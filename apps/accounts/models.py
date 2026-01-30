import uuid
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.db import models


# ====Teams ====
class Teams(models.Model):
    name = models.CharField(max_length=50)
    # 自動割当のときに、is_open=True のチームだけから選び、8人に達したら False にする想定
    is_open = models.BooleanField(default=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# ==== UserManager （ユーザー作成のルール）====
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, display_name=None, **extra_fields):
        if not email:
            raise ValueError("email is required")
        if not display_name:
            raise ValueError("display_name is required")
        
        email = self.normalize_email(email)
        user = self.model(email=email, display_name=display_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, display_name=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, display_name, **extra_fields)

# ==== User ====
class UserProfiles(AbstractBaseUser, PermissionsMixin):

    user_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(unique=True)

    display_name = models.CharField(max_length=50)
    
    team = models.ForeignKey("accounts.Teams", null=True, blank=True, on_delete=models.SET_NULL)

    last_recovery_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    def __str__(self):
        return self.email
    

class TicketSource(models.TextChoices):
    INITIAL_GRANT = "INITIAL_GRANT", "Initial grant"
    RESERVATION_DEPOSIT = "RESERVATION_DEPOSIT", "Reservation deposit"
    DEPOSIT_RETURN = "DEPOSIT_RETURN", "Deposit return"
    ADMIN_BONUS = "ADMIN_BONUS", "Admin bonus"
    FAIL_TO_TEAM_POOL = "FAIL_TO_TEAM_POOL", "Fail to team pool"

class TicketTransaction(models.Model):
    class OwnerType(models.TextChoices):
        USER = "USER", "User"
        TEAM = "TEAM", "Team"
    
    # USER or TEAM
    owner_type = models.CharField(max_length=10, choices=OwnerType.choices)

    # 片方だけ必須（CheckConstraintで担保）
    user = models.ForeignKey("accounts.UserProfiles", null=True, blank=True, on_delete=models.CASCADE)
    team = models.ForeignKey("accounts.Teams", null=True, blank=True, on_delete=models.CASCADE)

    # 予約に紐づく場合のみ入れる（初期付与等はNULL）
    # 以下、class Reservation が作成されてからマイグレーション
    # reservation = models.ForeignKey("reservations.Reservation", null=True, blank=True, on_delete=models.CASCADE)

    # 重複防止用の参照キー（初期付与はNULLでOK）
    ref_type = models.CharField(max_length=30, null=True, blank=True)
    ref_id = models.CharField(max_length=64, null=True, blank=True)

    # 取引の種類（固定choices）
    source = models.CharField(max_length=30, choices=TicketSource.choices)

    # 変動量（+1 / -1）
    amount = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # USERならuserのみ必須 / TEAMならteamのみ必須
            models.CheckConstraint(
                condition=(
                    (models.Q(owner_type="USER") & models.Q(user__isnull=False) & models.Q(team__isnull=True)) |
                    (models.Q(owner_type="TEAM") & models.Q(team__isnull=False) & models.Q(user__isnull=True))
                ),
                name="ticket_owner_match",
            ),
            # 同一参照の二重書き込み防止
            models.UniqueConstraint(
                fields=["owner_type", "user", "team", "source", "ref_type", "ref_id"],
                name="uniq_ticket_ref",
            ),
        ]