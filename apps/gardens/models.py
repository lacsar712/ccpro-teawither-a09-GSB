from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Garden(models.Model):
    name = models.CharField("茶园名称", max_length=120)
    altitudeBand = models.CharField("海拔带", max_length=60)
    notes = models.TextField("备注", blank=True, default="")

    class Meta:
        ordering = ["name"]
        verbose_name = "茶园"
        verbose_name_plural = "茶园"

    def __str__(self):
        return self.name


class Trough(models.Model):
    STATUS_LOADING = "loading"
    STATUS_WITHERING = "withering"
    STATUS_READY = "ready"
    STATUS_CHOICES = [
        (STATUS_LOADING, "装叶中"),
        (STATUS_WITHERING, "萎凋中"),
        (STATUS_READY, "可下槽"),
    ]

    garden = models.ForeignKey(
        Garden,
        on_delete=models.CASCADE,
        related_name="troughs",
        verbose_name="茶园",
    )
    troughCode = models.CharField("槽位编号", max_length=40)
    cultivar = models.CharField("茶树品种", max_length=80)
    loadKg = models.DecimalField("装叶量(kg)", max_digits=10, decimal_places=2)
    status = models.CharField(
        "状态",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_LOADING,
    )

    class Meta:
        ordering = ["garden__name", "troughCode"]
        verbose_name = "萎凋槽"
        verbose_name_plural = "萎凋槽"
        constraints = [
            models.UniqueConstraint(
                fields=["garden", "troughCode"],
                name="uniq_trough_code_per_garden",
            ),
        ]

    def __str__(self):
        return f"{self.garden.name}-{self.troughCode}"

    def latest_batch(self):
        return self.batches.order_by("-startedAt", "-id").first()

    def clean(self):
        super().clean()
        if self.status != self.STATUS_READY:
            return
        latest = None
        if self.pk:
            latest = (
                WitherBatch.objects.filter(trough_id=self.pk)
                .order_by("-startedAt", "-id")
                .first()
            )
        if latest is None or latest.actualMoisture is None or latest.actualMoisture > 40:
            raise ValidationError(
                {
                    "status": "无法设为可下槽：最新萎凋批次的实测含水率为空或高于 40%。"
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class WitherBatch(models.Model):
    trough = models.ForeignKey(
        Trough,
        on_delete=models.CASCADE,
        related_name="batches",
        verbose_name="萎凋槽",
    )
    startedAt = models.DateTimeField("开始时间")
    targetMoisture = models.DecimalField(
        "目标含水率(%)", max_digits=5, decimal_places=2
    )
    actualMoisture = models.DecimalField(
        "实测含水率(%)",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    rollGrade = models.CharField("揉捻等级", max_length=40)

    class Meta:
        ordering = ["-startedAt", "-id"]
        verbose_name = "萎凋批次"
        verbose_name_plural = "萎凋批次"

    def __str__(self):
        return f"{self.trough} @ {self.startedAt:%Y-%m-%d %H:%M}"


class LeafProvenance(models.Model):
    """茶青溯源条：一批一條，园批一致。

    删除策略：
    - 茶园(garden)：PROTECT —— 仍有溯源条的茶园拒绝删除；
    - 批次(batch)：CASCADE —— 删除批次时级联删除其溯源条。
    """

    garden = models.ForeignKey(
        Garden,
        on_delete=models.PROTECT,
        related_name="strips",
        verbose_name="所属茶园",
    )
    batch = models.OneToOneField(
        WitherBatch,
        on_delete=models.CASCADE,
        related_name="strip",
        verbose_name="关联批次",
    )
    villageGroup = models.CharField("鲜叶村组", max_length=120)
    pickingDate = models.DateField("采摘日")
    registrar = models.CharField("登记人", max_length=80)

    class Meta:
        ordering = ["-pickingDate", "-id"]
        verbose_name = "茶青溯源条"
        verbose_name_plural = "茶青溯源条"

    def __str__(self):
        return f"{self.garden.name}·{self.villageGroup} @ {self.pickingDate:%Y-%m-%d}"

    def clean(self):
        super().clean()
        errors = {}
        batch = self.batch if self.batch_id else None
        if batch is not None and self.garden_id is not None:
            if batch.trough.garden_id != self.garden_id:
                errors["batch"] = (
                    "关联批次所属槽位的茶园"
                    f"（{batch.trough.garden.name}）与条上茶园不一致。"
                )
        if batch is not None and self.pickingDate:
            # 批次开始日按东八区（Asia/Shanghai）日期口径比较
            start_date = timezone.localtime(batch.startedAt).date()
            if self.pickingDate > start_date:
                errors["pickingDate"] = (
                    "采摘日不得晚于批次开始日的东八区日期"
                    f"（{start_date:%Y-%m-%d}）。"
                )
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
