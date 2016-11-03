# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-02 20:25
from __future__ import unicode_literals

from django.db import migrations

def data_migration(apps, schema_editor):
    Abo = apps.get_model("my_ortoloco", "Abo")
    ExtraAbo = apps.get_model("my_ortoloco", "ExtraAbo")
    for abo in Abo.objects.all():
        for extra in abo.extra_abos:
            extra_abo = ExtraAbo.create()
            extra_abo.abo = abo
            extra_abo.type = extra
            extra_abo.active = True
            extra_abo.save()
        for extra in abo.future_extra_abos:
            extra_abo = ExtraAbo.create()
            extra_abo.abo = abo
            extra_abo.type = extra
            extra_abo.active = False
            extra_abo.save()
        

class Migration(migrations.Migration):

    dependencies = [
        ('my_ortoloco', '0016_auto_20161103_2038'),
    ]

    operations = [
        migrations.RunPython(data_migration),
    ]