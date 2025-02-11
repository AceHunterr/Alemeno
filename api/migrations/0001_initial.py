# Generated by Django 5.1.3 on 2024-11-11 20:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("customer_id", models.AutoField(primary_key=True, serialize=False)),
                ("first_name", models.CharField(max_length=50)),
                ("last_name", models.CharField(max_length=50)),
                ("phone_number", models.CharField(max_length=15)),
                ("age", models.IntegerField()),
                (
                    "monthly_salary",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("approved_limit", models.IntegerField()),
                (
                    "current_debt",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Loan",
            fields=[
                ("loan_id", models.AutoField(primary_key=True, serialize=False)),
                ("loan_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("tenure", models.IntegerField()),
                ("interest_rate", models.DecimalField(decimal_places=2, max_digits=4)),
                (
                    "monthly_repayment",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("emi_paid_on_time", models.BooleanField()),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="api.customer"
                    ),
                ),
            ],
        ),
    ]
