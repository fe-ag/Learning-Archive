from django.conf import settings

from .models import Category, Page


def site(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_TAGLINE": settings.SITE_TAGLINE,
        "nav_categories": Category.objects.with_published_count().filter(
            published_count__gt=0
        ),
        "menu_pages": Page.objects.filter(is_published=True, show_in_menu=True),
    }
