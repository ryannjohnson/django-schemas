# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_schemas.models
import tests.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Test1AUser',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('db', models.CharField(max_length=63)),
            ],
            options={
                'db_environment': 'test1-a',
            },
            bases=(django_schemas.models.BaseModel, models.Model, tests.models.Test1AUserActions),
        ),
        migrations.CreateModel(
            name='Test1BUser',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('master_id', models.BigIntegerField(unique=True)),
                ('color', models.CharField(max_length=100, default='grey')),
            ],
            options={
                'db_environment': 'test1-b',
            },
            bases=(django_schemas.models.BaseModel, models.Model),
        ),
    ]
