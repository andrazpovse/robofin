# Generated by Django 3.1.7 on 2021-08-09 04:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0002_auto_20210728_1012'),
    ]

    operations = [
        migrations.AddField(
            model_name='portfolio',
            name='risk_score',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
