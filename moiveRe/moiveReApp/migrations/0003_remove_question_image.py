# Generated by Django 5.0.2 on 2024-03-02 10:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('moiveReApp', '0002_question_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='image',
        ),
    ]
