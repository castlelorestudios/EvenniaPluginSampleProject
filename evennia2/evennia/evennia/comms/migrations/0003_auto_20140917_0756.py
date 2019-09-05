# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('objects', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('typeclasses', '0001_initial'),
        ('comms', '0002_msg_db_hide_from_objects'),
    ]

    operations = [
        migrations.AddField(
            model_name='msg',
            name='db_hide_from_accounts',
            field=models.ManyToManyField(related_name=b'hide_from_accounts_set', null=True, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='msg',
            name='db_receivers_channels',
            field=models.ManyToManyField(help_text=b'channel recievers', related_name=b'channel_set', null=True, to='comms.ChannelDB'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='msg',
            name='db_receivers_objects',
            field=models.ManyToManyField(help_text=b'object receivers', related_name=b'receiver_object_set', null=True, to='objects.ObjectDB'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='msg',
            name='db_receivers_accounts',
            field=models.ManyToManyField(help_text=b'account receivers', related_name=b'receiver_account_set', null=True, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='msg',
            name='db_sender_objects',
            field=models.ManyToManyField(related_name=b'sender_object_set', null=True, verbose_name=b'sender(object)', to='objects.ObjectDB', db_index=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='msg',
            name='db_sender_accounts',
            field=models.ManyToManyField(related_name=b'sender_account_set', null=True, verbose_name=b'sender(account)', to=settings.AUTH_USER_MODEL, db_index=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='channeldb',
            name='db_attributes',
            field=models.ManyToManyField(help_text=b'attributes on this object. An attribute can hold any pickle-able python object (see docs for special cases).', to='typeclasses.Attribute', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='channeldb',
            name='db_subscriptions',
            field=models.ManyToManyField(related_name=b'subscription_set', null=True, verbose_name=b'subscriptions', to=settings.AUTH_USER_MODEL, db_index=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='channeldb',
            name='db_tags',
            field=models.ManyToManyField(help_text=b'tags on this object. Tags are simple string markers to identify, group and alias objects.', to='typeclasses.Tag', null=True),
            preserve_default=True,
        ),
    ]
