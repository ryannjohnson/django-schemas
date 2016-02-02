# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_schemas.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Test1AUser',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('db', models.CharField(max_length=63)),
            ],
            options={
                'db_environment': 'test1-a',
            },
            bases=(django_schemas.models.BaseModel, models.Model),
        ),
        migrations.CreateModel(
            name='Test1BUser',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('master_id', models.BigIntegerField(unique=True)),
                ('favorite_color', models.CharField(default='grey', max_length=100)),
            ],
            options={
                'db_environment': 'test1-b',
            },
            bases=(django_schemas.models.BaseModel, models.Model),
        ),
    ]
