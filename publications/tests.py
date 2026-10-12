import tempfile
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Category, Page, Publication


def make_publication(category, title, **kwargs):
    defaults = {
        "kind": "article",
        "summary": f"Summary of {title}",
        "body": f"Body of {title}",
        "status": "published",
        "published_at": timezone.now() - timedelta(days=1),
    }
    defaults.update(kwargs)
    return Publication.objects.create(title=title, category=category, **defaults)


class ModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Teaching Methods")

    def test_category_slug_is_generated(self):
        self.assertEqual(self.category.slug, "teaching-methods")

    def test_duplicate_titles_get_unique_slugs(self):
        first = make_publication(self.category, "Same Title")
        second = make_publication(self.category, "Same Title")
        self.assertEqual(first.slug, "same-title")
        self.assertEqual(second.slug, "same-title-2")

    def test_published_at_is_set_when_published(self):
        publication = Publication.objects.create(
            title="Auto date", category=self.category, summary="s", body="b", status="published"
        )
        self.assertIsNotNone(publication.published_at)

    def test_draft_has_no_published_date(self):
        publication = make_publication(self.category, "Draft", status="draft", published_at=None)
        self.assertIsNone(publication.published_at)

    def test_published_queryset_hides_drafts_and_future_items(self):
        live = make_publication(self.category, "Live")
        make_publication(self.category, "Draft", status="draft", published_at=None)
        make_publication(self.category, "Future", published_at=timezone.now() + timedelta(days=2))
        self.assertEqual(list(Publication.objects.published()), [live])

    def test_category_cannot_be_deleted_while_in_use(self):
        from django.db.models import ProtectedError

        make_publication(self.category, "Uses category")
        with self.assertRaises(ProtectedError):
            self.category.delete()


class PublicSiteTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Assessment", description="About assessment.")
        self.other = Category.objects.create(name="Curriculum")
        self.live = make_publication(self.category, "Rubrics guide", authors="Ada Lovelace")
        self.paper = make_publication(self.other, "Outcome planning", kind="paper")
        self.draft = make_publication(self.category, "Secret draft", status="draft", published_at=None)
        self.future = make_publication(
            self.category, "Future piece", published_at=timezone.now() + timedelta(days=3)
        )

    def test_home_page_renders(self):
        response = self.client.get(reverse("publications:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rubrics guide")
        self.assertNotContains(response, "Secret draft")

    def test_list_only_shows_published_items(self):
        response = self.client.get(reverse("publications:list"))
        self.assertContains(response, "Rubrics guide")
        self.assertContains(response, "Outcome planning")
        self.assertNotContains(response, "Secret draft")
        self.assertNotContains(response, "Future piece")

    def test_search_by_title_and_author(self):
        response = self.client.get(reverse("publications:list"), {"q": "rubrics"})
        self.assertContains(response, "Rubrics guide")
        self.assertNotContains(response, "Outcome planning")
        response = self.client.get(reverse("publications:list"), {"q": "lovelace"})
        self.assertContains(response, "Rubrics guide")

    def test_search_with_no_matches_shows_empty_state(self):
        response = self.client.get(reverse("publications:list"), {"q": "zzzz-nothing"})
        self.assertContains(response, "No publications match")

    def test_filter_by_kind(self):
        response = self.client.get(reverse("publications:list"), {"kind": "paper"})
        self.assertContains(response, "Outcome planning")
        self.assertNotContains(response, "Rubrics guide")

    def test_invalid_kind_is_ignored(self):
        response = self.client.get(reverse("publications:list"), {"kind": "bogus"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rubrics guide")

    def test_filter_by_category_query_parameter(self):
        response = self.client.get(reverse("publications:list"), {"category": "curriculum"})
        self.assertContains(response, "Outcome planning")
        self.assertNotContains(response, "Rubrics guide")

    def test_category_page(self):
        response = self.client.get(self.category.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "About assessment.")
        self.assertContains(response, "Rubrics guide")
        self.assertNotContains(response, "Outcome planning")

    def test_unknown_category_returns_404(self):
        response = self.client.get(reverse("publications:category", args=["missing"]))
        self.assertEqual(response.status_code, 404)

    def test_sorting_by_title(self):
        response = self.client.get(reverse("publications:list"), {"sort": "title"})
        titles = [p.title for p in response.context["publications"]]
        self.assertEqual(titles, sorted(titles))

    def test_pagination(self):
        for index in range(15):
            make_publication(self.category, f"Bulk item {index:02d}")
        first = self.client.get(reverse("publications:list"))
        self.assertEqual(len(first.context["publications"]), 12)
        second = self.client.get(reverse("publications:list"), {"page": 2})
        self.assertEqual(second.status_code, 200)
        self.assertTrue(len(second.context["publications"]) > 0)
        self.assertEqual(self.client.get(reverse("publications:list"), {"page": 99}).status_code, 404)

    def test_detail_page_for_published_item(self):
        response = self.client.get(self.live.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Body of Rubrics guide")
        self.assertContains(response, '<link rel="canonical"')

    def test_detail_page_hides_draft_and_scheduled_items(self):
        self.assertEqual(self.client.get(self.draft.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.get(self.future.get_absolute_url()).status_code, 404)

    def test_body_is_escaped(self):
        make_publication(self.category, "Escaping check", body="<script>alert(1)</script>")
        response = self.client.get(reverse("publications:detail", args=["escaping-check"]))
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_page_visibility(self):
        shown = Page.objects.create(title="About", content="About text", show_in_menu=True)
        hidden = Page.objects.create(title="Hidden", content="Nope", is_published=False)
        self.assertEqual(self.client.get(shown.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(hidden.get_absolute_url()).status_code, 404)
        self.assertContains(self.client.get(reverse("publications:home")), "About")

    def test_sitemap_lists_only_published_items(self):
        response = self.client.get(reverse("sitemap"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.live.get_absolute_url())
        self.assertNotContains(response, self.draft.get_absolute_url())

    def test_robots_txt_blocks_management_area(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Disallow: /manage/")
        self.assertContains(response, "sitemap.xml")

    def test_missing_page_uses_custom_404(self):
        response = self.client.get("/does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)


class AttachmentTests(TestCase):
    def test_download_link_is_shown(self):
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            category = Category.objects.create(name="Files")
            publication = make_publication(
                category,
                "With file",
                attachment=SimpleUploadedFile("paper.pdf", b"%PDF-1.4 test"),
            )
            response = self.client.get(publication.get_absolute_url())
            self.assertContains(response, "Download PDF")

    def test_attachment_is_removed_when_publication_is_deleted(self):
        import os

        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            category = Category.objects.create(name="Files")
            publication = make_publication(
                category, "Remove me", attachment=SimpleUploadedFile("gone.pdf", b"data")
            )
            path = publication.attachment.path
            self.assertTrue(os.path.exists(path))
            publication.delete()
            self.assertFalse(os.path.exists(path))
