# Generated by Django 5.1.3 on 2024-11-21 19:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_section_assignment_studentwork_student_file_path_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assignment',
            name='markscheme',
        ),
        migrations.RemoveField(
            model_name='studentwork',
            name='student_file',
        ),
    ]
