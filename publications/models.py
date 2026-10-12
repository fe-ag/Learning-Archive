import os

from django.db import models
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .validators import validate_attachment


def unique_slug(model, value, max_length, pk=None):
    """Build a slug from ``value`` that is unique for ``model``."""
    base = slugify(value)[:max_length] or "item"
    slug = base
    counter = 2
    queryset = model.objects.all()
    if pk:
        queryset = queryset.exclude(pk=pk)
    while queryset.filter(slug=slug).exists():
        suffix = f"-{counter}"
        slug = base[: max_length - len(suffix)] + suffix
        counter += 1
    return slug


class CategoryQuerySet(models.QuerySet):
    def with_published_count(self):
        return self.annotate(
            published_count=Count(
                "publications",
                filter=Q(
                    publications__status="published",
                    publications__published_at__lte=timezone.now(),
                ),
            )
        )


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CategoryQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Category, self.name, 140, self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("publications:category", args=[self.slug])


class PublicationQuerySet(models.QuerySet):
    def published(self):
        """Publications that are marked as published and whose date has arrived."""
        return self.filter(status="published", published_at__lte=timezone.now())


class Publication(models.Model):
    class Kind(models.TextChoices):
        ARTICLE = "article", "Article"
        PAPER = "paper", "Paper"
        RESOURCE = "resource", "Learning resource"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.ARTICLE)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="publications"
    )
    authors = models.CharField(max_length=300, blank=True)
    summary = models.TextField(max_length=600)
    body = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to="publications/%Y/%m/",
        blank=True,
        validators=[validate_attachment],
    )
    external_url = models.URLField(max_length=500, blank=True)
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.DRAFT
    )
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PublicationQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "published_at"], name="pub_status_date_idx"),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Publication, self.title, 220, self.pk)
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("publications:detail", args=[self.slug])

    @property
    def is_live(self):
        return (
            self.status == self.Status.PUBLISHED
            and self.published_at is not None
            and self.published_at <= timezone.now()
        )

    @property
    def attachment_name(self):
        return os.path.basename(self.attachment.name) if self.attachment else ""

    @property
    def attachment_type(self):
        if not self.attachment:
            return ""
        return os.path.splitext(self.attachment.name)[1].lstrip(".").upper()


class Page(models.Model):
    """Simple editable page such as About or Contact."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    content = models.TextField()
    meta_description = models.CharField(max_length=160, blank=True)
    is_published = models.BooleanField(default=True)
    show_in_menu = models.BooleanField(default=False)
    menu_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["menu_order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Page, self.title, 220, self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("publications:page", args=[self.slug])
