import django.db.models.deletion
from django.db import migrations, models

import publications.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=140, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name_plural": "categories",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Page",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(blank=True, max_length=220, unique=True)),
                ("content", models.TextField()),
                ("meta_description", models.CharField(blank=True, max_length=160)),
                ("is_published", models.BooleanField(default=True)),
                ("show_in_menu", models.BooleanField(default=False)),
                ("menu_order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["menu_order", "title"],
            },
        ),
        migrations.CreateModel(
            name="Publication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(blank=True, max_length=220, unique=True)),
                ("kind", models.CharField(choices=[("article", "Article"), ("paper", "Paper"), ("resource", "Learning resource")], default="article", max_length=20)),
                ("authors", models.CharField(blank=True, max_length=300)),
                ("summary", models.TextField(max_length=600)),
                ("body", models.TextField(blank=True)),
                ("attachment", models.FileField(blank=True, upload_to="publications/%Y/%m/", validators=[publications.validators.validate_attachment])),
                ("external_url", models.URLField(blank=True, max_length=500)),
                ("meta_title", models.CharField(blank=True, max_length=70)),
                ("meta_description", models.CharField(blank=True, max_length=160)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published")], default="draft", max_length=12)),
                ("is_featured", models.BooleanField(default=False)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="publications", to="publications.category")),
            ],
            options={
                "ordering": ["-published_at", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="publication",
            index=models.Index(fields=["status", "published_at"], name="pub_status_date_idx"),
        ),
    ]
