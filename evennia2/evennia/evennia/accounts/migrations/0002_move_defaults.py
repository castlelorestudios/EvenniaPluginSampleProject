# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def convert_defaults(apps, schema_editor):
    AccountDB = apps.get_model("accounts", "AccountDB")
    for account in AccountDB.objects.filter(db_typeclass_path="src.accounts.account.Account"):
        account.db_typeclass_path = "typeclasses.accounts.Account"
        account.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(convert_defaults),
    ]
