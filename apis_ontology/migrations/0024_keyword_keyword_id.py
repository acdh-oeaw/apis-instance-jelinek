# Generated by Django 4.1.8 on 2023-05-16 08:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apis_ontology', '0023_xml_content_dump'),
    ]

    operations = [
        migrations.AddField(
            model_name='keyword',
            name='keyword_id',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]
