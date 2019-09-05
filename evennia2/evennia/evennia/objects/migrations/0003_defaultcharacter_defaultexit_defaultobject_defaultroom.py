# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('objects', '0002_auto_20140917_0756'),
    ]

    operations = [
        migrations.CreateModel(
            name='DefaultObject',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('objects.objectdb',),
        ),
        migrations.CreateModel(
            name='DefaultExit',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('objects.defaultobject',),
        ),
        migrations.CreateModel(
            name='DefaultCharacter',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('objects.defaultobject',),
        ),
        migrations.CreateModel(
            name='DefaultRoom',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('objects.defaultobject',),
        ),
    ]
