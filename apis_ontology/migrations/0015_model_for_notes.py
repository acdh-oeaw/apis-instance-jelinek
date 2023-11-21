# Generated by Django 3.1.14 on 2022-03-17 22:26

from dataclasses import Field
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        
        ('apis_ontology', '0014_change_notes_to_text_field'),
    ]

    operations = [
        migrations.CreateModel(
            name="XMLNote",
            fields=[
                ('tempentityclass_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='apis_entities.tempentityclass')),
                ("content", models.TextField(blank=True, null=True)),
                ("rendition", models.CharField(max_length=1024, blank=True, null=True)),
                ("type", models.CharField(max_length=1024, blank=True, null=True))
            ],
            options={
                'abstract': False,
            },
            bases=('apis_entities.tempentityclass',)
        )
    ]
