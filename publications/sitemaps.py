from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Category, Page, Publication


class StaticSitemap(Sitemap):
    priority = 0.8
    changefreq = "daily"

    def items(self):
        return ["publications:home", "publications:list"]

    def location(self, item):
        return reverse(item)


class PublicationSitemap(Sitemap):
    priority = 0.7
    changefreq = "monthly"

    def items(self):
        return Publication.objects.published()

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    priority = 0.6
    changefreq = "weekly"

    def items(self):
        return Category.objects.with_published_count().filter(published_count__gt=0)

    def lastmod(self, obj):
        return obj.updated_at


class PageSitemap(Sitemap):
    priority = 0.4
    changefreq = "yearly"

    def items(self):
        return Page.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    "static": StaticSitemap,
    "publications": PublicationSitemap,
    "categories": CategorySitemap,
    "pages": PageSitemap,
}
