from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Garden, LeafProvenance, Trough, WitherBatch


def ensure_seed_data():
    """Idempotent seed: users + sample gardens/troughs/batches/strips."""
    User = get_user_model()

    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@teawither.local", "123456")

    if not User.objects.filter(username="witherer").exists():
        User.objects.create_user("witherer", "witherer@teawither.local", "123456")

    if not Garden.objects.exists():
        _seed_gardens_troughs_batches()

    _ensure_strips()


def _seed_gardens_troughs_batches():
    g1 = Garden.objects.create(
        name="云雾岭一号园",
        altitudeBand="800-1000m",
        notes="向阳坡，晨雾较重",
    )
    g2 = Garden.objects.create(
        name="竹影台二号园",
        altitudeBand="600-800m",
        notes="背风缓坡",
    )

    t1 = Trough.objects.create(
        garden=g1,
        troughCode="A-01",
        cultivar="福鼎大白",
        loadKg=Decimal("120.50"),
        status=Trough.STATUS_WITHERING,
    )
    t2 = Trough.objects.create(
        garden=g1,
        troughCode="A-02",
        cultivar="铁观音",
        loadKg=Decimal("95.00"),
        status=Trough.STATUS_LOADING,
    )
    t3 = Trough.objects.create(
        garden=g2,
        troughCode="B-01",
        cultivar="黄金芽",
        loadKg=Decimal("88.25"),
        status=Trough.STATUS_WITHERING,
    )

    now = timezone.now()
    WitherBatch.objects.create(
        trough=t1,
        startedAt=now - timezone.timedelta(hours=18),
        targetMoisture=Decimal("38.00"),
        actualMoisture=Decimal("37.50"),
        rollGrade="一级",
    )
    WitherBatch.objects.create(
        trough=t2,
        startedAt=now - timezone.timedelta(hours=2),
        targetMoisture=Decimal("40.00"),
        actualMoisture=None,
        rollGrade="待评",
    )
    WitherBatch.objects.create(
        trough=t3,
        startedAt=now - timezone.timedelta(hours=30),
        targetMoisture=Decimal("36.00"),
        actualMoisture=Decimal("42.00"),
        rollGrade="二级",
    )

    # Ready trough with valid moisture
    t4 = Trough.objects.create(
        garden=g2,
        troughCode="B-02",
        cultivar="龙井43",
        loadKg=Decimal("110.00"),
        status=Trough.STATUS_WITHERING,
    )
    WitherBatch.objects.create(
        trough=t4,
        startedAt=now - timezone.timedelta(hours=24),
        targetMoisture=Decimal("35.00"),
        actualMoisture=Decimal("34.80"),
        rollGrade="特级",
    )
    t4.status = Trough.STATUS_READY
    t4.save()


def _ensure_strips():
    """两园多条溯源条；幂等：已有溯源条则跳过。"""
    if LeafProvenance.objects.exists():
        return
    batches = list(
        WitherBatch.objects.select_related("trough", "trough__garden").order_by("id")
    )
    villages = ["云岭村一组", "云岭村二组", "竹坪村三组", "竹坪村四组"]
    for i, batch in enumerate(batches):
        # 园批一致：条上茶园直接取批次槽位所属茶园；
        # 采摘日取批次开始日的东八区日期，满足“不晚于”规则。
        LeafProvenance.objects.create(
            garden=batch.trough.garden,
            batch=batch,
            villageGroup=villages[i % len(villages)],
            pickingDate=timezone.localtime(batch.startedAt).date(),
            registrar="witherer" if i % 2 == 0 else "admin",
        )
