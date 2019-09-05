# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('objects', '0001_initial'),
        ('comms', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='msg',
            name='db_hide_from_objects',
            field=models.ManyToManyField(related_name=b'hide_from_objects_set', null=True, to='objects.ObjectDB'),
            preserve_default=True,
        ),
    ]
