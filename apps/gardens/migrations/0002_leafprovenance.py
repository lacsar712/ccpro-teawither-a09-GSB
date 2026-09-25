# Generated for TeaWither leaf provenance strips (A09)

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gardens", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LeafProvenance",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("villageGroup", models.CharField(max_length=120, verbose_name="鲜叶村组")),
                ("pickedOn", models.DateField(verbose_name="采摘日")),
                ("registrar", models.CharField(max_length=60, verbose_name="登记人")),
                (
                    "garden",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="provenances",
                        to="gardens.garden",
                        verbose_name="所属茶园",
                    ),
                ),
                (
                    "batch",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="provenance",
                        to="gardens.witherbatch",
                        verbose_name="关联批次",
                    ),
                ),
            ],
            options={
                "verbose_name": "茶青溯源条",
                "verbose_name_plural": "茶青溯源条",
                "ordering": ["-pickedOn", "-id"],
            },
        ),
    ]
