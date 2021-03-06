# Generated by Django 3.1.7 on 2021-07-21 12:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0001_initial'),
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userinfo',
            name='monthly_investment',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='portfolio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='portfolio.portfolio'),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='risk_score',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
