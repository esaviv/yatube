# Generated by Django 2.2.16 on 2022-12-30 12:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0012_auto_20221230_1449'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'default_related_name': 'posts', 'ordering': ('-created',)},
        ),
    ]
