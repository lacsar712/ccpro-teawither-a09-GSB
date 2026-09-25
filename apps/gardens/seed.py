from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Garden, LeafProvenance, Trough, WitherBatch


def ensure_seed_data():
    """Idempotent seed: users + sample gardens/troughs/batches."""
    User = get_user_model()

    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@teawither.local", "123456")

    if not User.objects.filter(username="witherer").exists():
        User.objects.create_user("witherer", "witherer@teawither.local", "123456")

    if Garden.objects.exists():
        return

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
    b1 = WitherBatch.objects.create(
        trough=t1,
        startedAt=now - timezone.timedelta(hours=18),
        targetMoisture=Decimal("38.00"),
        actualMoisture=Decimal("37.50"),
        rollGrade="一级",
    )
    b2 = WitherBatch.objects.create(
        trough=t2,
        startedAt=now - timezone.timedelta(hours=2),
        targetMoisture=Decimal("40.00"),
        actualMoisture=None,
        rollGrade="待评",
    )
    b3 = WitherBatch.objects.create(
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
    b4 = WitherBatch.objects.create(
        trough=t4,
        startedAt=now - timezone.timedelta(hours=24),
        targetMoisture=Decimal("35.00"),
        actualMoisture=Decimal("34.80"),
        rollGrade="特级",
    )
    t4.status = Trough.STATUS_READY
    t4.save()

    # 茶青溯源条：两园多条，一批次一条，园批一致，采摘日不晚于批次开始日
    def picked(batch, days_before=0):
        local_date = timezone.localtime(batch.startedAt).date()
        return local_date - timezone.timedelta(days=days_before)

    LeafProvenance.objects.create(
        garden=g1,
        batch=b1,
        villageGroup="云雾村一组",
        pickedOn=picked(b1),
        registrar="张采青",
    )
    LeafProvenance.objects.create(
        garden=g1,
        batch=b2,
        villageGroup="云雾村二组",
        pickedOn=picked(b2),
        registrar="李露生",
    )
    LeafProvenance.objects.create(
        garden=g2,
        batch=b3,
        villageGroup="竹影村三组",
        pickedOn=picked(b3, days_before=1),
        registrar="王雾根",
    )
    LeafProvenance.objects.create(
        garden=g2,
        batch=b4,
        villageGroup="竹影村一组",
        pickedOn=picked(b4),
        registrar="赵芽农",
    )
