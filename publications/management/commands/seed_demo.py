from django.core.management.base import BaseCommand
from django.utils import timezone

from publications.models import Category, Page, Publication

CATEGORIES = [
    ("Teaching Methods", "Research and practice notes on how people learn and how to teach well."),
    ("Curriculum Design", "Frameworks, syllabi and planning guides for courses and programmes."),
    ("Assessment", "Approaches to measuring learning fairly and usefully."),
]

PUBLICATIONS = [
    ("Spaced Practice in the Classroom", "article", "Teaching Methods", "A. Example", True,
     "A short guide to scheduling review so that students remember more with less effort."),
    ("Designing a Course Around Outcomes", "paper", "Curriculum Design", "B. Sample, C. Demo", True,
     "How to plan a course by starting from what learners should be able to do."),
    ("Rubrics That Students Actually Use", "resource", "Assessment", "D. Placeholder", False,
     "A template and a worked example for writing clear, usable rubrics."),
]


class Command(BaseCommand):
    help = "Create sample categories, publications and pages for a local try-out. Safe to run twice."

    def handle(self, *args, **options):
        categories = {}
        for name, description in CATEGORIES:
            category, _ = Category.objects.get_or_create(name=name, defaults={"description": description})
            categories[name] = category

        for title, kind, category_name, authors, featured, summary in PUBLICATIONS:
            Publication.objects.get_or_create(
                title=title,
                defaults={
                    "kind": kind,
                    "category": categories[category_name],
                    "authors": authors,
                    "summary": summary,
                    "body": summary + "\n\nThis is sample content created by the seed_demo command. Replace it from the management area.",
                    "status": Publication.Status.PUBLISHED,
                    "published_at": timezone.now(),
                    "is_featured": featured,
                },
            )

        Page.objects.get_or_create(
            title="About",
            defaults={
                "content": "Tell visitors who you are and what this archive is for.\n\nEdit this page from the management area.",
                "meta_description": "About this archive.",
                "show_in_menu": True,
                "menu_order": 1,
            },
        )
        self.stdout.write(self.style.SUCCESS("Sample content is in place."))
