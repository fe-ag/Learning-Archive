import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from publications.models import Category, Page, Publication

User = get_user_model()


class DashboardBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user("editor", password="Str0ng-pass-123", is_staff=True)
        cls.visitor = User.objects.create_user("reader", password="Str0ng-pass-123")
        cls.category = Category.objects.create(name="Assessment")

    def login_staff(self):
        self.client.force_login(self.staff)

    def make_publication(self, title="Existing", **kwargs):
        defaults = {
            "kind": "article",
            "summary": "A summary",
            "body": "Some body",
            "status": "draft",
        }
        defaults.update(kwargs)
        return Publication.objects.create(title=title, category=self.category, **defaults)


class AccessControlTests(DashboardBase):
    PROTECTED = [
        "dashboard:index",
        "dashboard:publication_list",
        "dashboard:publication_create",
        "dashboard:category_list",
        "dashboard:category_create",
        "dashboard:page_list",
        "dashboard:page_create",
    ]

    def test_anonymous_users_are_redirected_to_login(self):
        for name in self.PROTECTED:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)
            self.assertIn(reverse("dashboard:login"), response["Location"], name)

    def test_signed_in_non_staff_users_get_403(self):
        self.client.force_login(self.visitor)
        for name in self.PROTECTED:
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)

    def test_non_staff_cannot_post_changes(self):
        self.client.force_login(self.visitor)
        response = self.client.post(reverse("dashboard:category_create"), {"name": "Hack"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Category.objects.filter(name="Hack").exists())

    def test_non_staff_cannot_toggle_or_delete(self):
        publication = self.make_publication()
        self.client.force_login(self.visitor)
        self.assertEqual(self.client.post(reverse("dashboard:publication_toggle", args=[publication.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("dashboard:publication_delete", args=[publication.pk])).status_code, 403)
        self.assertTrue(Publication.objects.filter(pk=publication.pk).exists())

    def test_staff_can_open_every_page(self):
        self.login_staff()
        for name in self.PROTECTED:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_post_without_csrf_token_is_rejected(self):
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.staff)
        response = strict.post(reverse("dashboard:category_create"), {"name": "No token"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Category.objects.filter(name="No token").exists())

    def test_django_admin_is_not_installed(self):
        from django.conf import settings

        self.assertNotIn("django.contrib.admin", settings.INSTALLED_APPS)
        self.assertEqual(self.client.get("/admin/").status_code, 404)


class LoginTests(DashboardBase):
    def test_staff_can_sign_in_and_out(self):
        response = self.client.post(
            reverse("dashboard:login"), {"username": "editor", "password": "Str0ng-pass-123"}
        )
        self.assertRedirects(response, reverse("dashboard:index"), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 200)
        response = self.client.post(reverse("dashboard:logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 302)

    def test_non_staff_cannot_sign_in(self):
        response = self.client.post(
            reverse("dashboard:login"), {"username": "reader", "password": "Str0ng-pass-123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "does not have access")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_wrong_password_is_rejected(self):
        response = self.client.post(
            reverse("dashboard:login"), {"username": "editor", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post(self):
        self.login_staff()
        self.assertEqual(self.client.get(reverse("dashboard:logout")).status_code, 405)


class CategoryManagementTests(DashboardBase):
    def setUp(self):
        self.login_staff()

    def test_create_category(self):
        response = self.client.post(
            reverse("dashboard:category_create"), {"name": "Curriculum", "description": "Plans"}, follow=True
        )
        self.assertContains(response, "“Curriculum” was created.")
        self.assertEqual(Category.objects.get(name="Curriculum").slug, "curriculum")

    def test_duplicate_category_name_is_rejected(self):
        response = self.client.post(reverse("dashboard:category_create"), {"name": "Assessment"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")

    def test_update_category(self):
        response = self.client.post(
            reverse("dashboard:category_update", args=[self.category.pk]),
            {"name": "Assessment & Feedback", "slug": "assessment", "description": ""},
            follow=True,
        )
        self.assertContains(response, "was saved")
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Assessment & Feedback")

    def test_delete_empty_category(self):
        empty = Category.objects.create(name="Empty")
        response = self.client.post(reverse("dashboard:category_delete", args=[empty.pk]), follow=True)
        self.assertContains(response, "was deleted")
        self.assertFalse(Category.objects.filter(pk=empty.pk).exists())

    def test_cannot_delete_category_in_use(self):
        self.make_publication()
        response = self.client.post(
            reverse("dashboard:category_delete", args=[self.category.pk]), follow=True
        )
        self.assertContains(response, "can’t be deleted")
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())

    def test_category_search(self):
        Category.objects.create(name="Zoology")
        response = self.client.get(reverse("dashboard:category_list"), {"q": "zoo"})
        self.assertContains(response, "Zoology")
        self.assertNotContains(response, ">Assessment<")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PublicationManagementTests(DashboardBase):
    def setUp(self):
        self.login_staff()

    def valid_data(self, **overrides):
        data = {
            "title": "New paper",
            "slug": "",
            "kind": "paper",
            "category": self.category.pk,
            "authors": "A. Author",
            "summary": "Short summary",
            "body": "Full text",
            "external_url": "",
            "meta_title": "",
            "meta_description": "",
            "status": "draft",
            "published_at": "",
        }
        data.update(overrides)
        return data

    def test_create_publication(self):
        response = self.client.post(reverse("dashboard:publication_create"), self.valid_data(), follow=True)
        self.assertContains(response, "“New paper” was created.")
        publication = Publication.objects.get(title="New paper")
        self.assertEqual(publication.slug, "new-paper")
        self.assertEqual(publication.status, "draft")

    def test_publishing_sets_date_and_makes_item_public(self):
        self.client.post(reverse("dashboard:publication_create"), self.valid_data(status="published"))
        publication = Publication.objects.get(title="New paper")
        self.assertIsNotNone(publication.published_at)
        self.assertEqual(self.client.get(publication.get_absolute_url()).status_code, 200)

    def test_future_date_schedules_publication(self):
        future = (timezone.now() + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M")
        self.client.post(
            reverse("dashboard:publication_create"),
            self.valid_data(status="published", published_at=future),
        )
        publication = Publication.objects.get(title="New paper")
        self.assertEqual(Publication.objects.published().count(), 0)
        self.assertEqual(self.client.get(publication.get_absolute_url()).status_code, 404)

    def test_required_fields_are_validated(self):
        response = self.client.post(reverse("dashboard:publication_create"), {"title": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.assertEqual(Publication.objects.count(), 0)

    def test_content_source_is_required(self):
        response = self.client.post(reverse("dashboard:publication_create"), self.valid_data(body=""))
        self.assertContains(response, "Add body text, upload a file, or provide an external link.")
        self.assertEqual(Publication.objects.count(), 0)

    def test_external_link_alone_is_enough(self):
        response = self.client.post(
            reverse("dashboard:publication_create"),
            self.valid_data(body="", external_url="https://example.org/paper"),
            follow=True,
        )
        self.assertContains(response, "was created")

    def test_external_link_must_be_http(self):
        response = self.client.post(
            reverse("dashboard:publication_create"),
            self.valid_data(external_url="ftp://example.org/file"),
        )
        self.assertContains(response, "http:// or https://")

    def test_upload_allowed_file(self):
        upload = SimpleUploadedFile("lesson.pdf", b"%PDF-1.4 content", content_type="application/pdf")
        response = self.client.post(
            reverse("dashboard:publication_create"), self.valid_data(body="", attachment=upload), follow=True
        )
        self.assertContains(response, "was created")
        self.assertTrue(Publication.objects.get(title="New paper").attachment.name.endswith(".pdf"))

    def test_upload_disallowed_file_type(self):
        upload = SimpleUploadedFile("script.exe", b"MZ", content_type="application/octet-stream")
        response = self.client.post(
            reverse("dashboard:publication_create"), self.valid_data(body="", attachment=upload)
        )
        self.assertContains(response, "are not allowed")
        self.assertEqual(Publication.objects.count(), 0)

    @override_settings(MAX_UPLOAD_MB=1)
    def test_upload_too_large(self):
        upload = SimpleUploadedFile("big.pdf", b"0" * (1024 * 1024 + 1))
        response = self.client.post(
            reverse("dashboard:publication_create"), self.valid_data(body="", attachment=upload)
        )
        self.assertContains(response, "larger than 1 MB")

    def test_update_publication(self):
        publication = self.make_publication("Old title")
        response = self.client.post(
            reverse("dashboard:publication_update", args=[publication.pk]),
            self.valid_data(title="Updated title", slug=publication.slug),
            follow=True,
        )
        self.assertContains(response, "“Updated title” was saved.")
        publication.refresh_from_db()
        self.assertEqual(publication.title, "Updated title")

    def test_duplicate_slug_is_rejected(self):
        self.make_publication("First")
        response = self.client.post(
            reverse("dashboard:publication_create"), self.valid_data(title="Second", slug="first")
        )
        self.assertContains(response, "already exists")

    def test_toggle_requires_post(self):
        publication = self.make_publication()
        response = self.client.get(reverse("dashboard:publication_toggle", args=[publication.pk]))
        self.assertEqual(response.status_code, 405)

    def test_toggle_publishes_and_unpublishes(self):
        publication = self.make_publication()
        url = reverse("dashboard:publication_toggle", args=[publication.pk])
        self.client.post(url)
        publication.refresh_from_db()
        self.assertEqual(publication.status, "published")
        self.assertIsNotNone(publication.published_at)
        self.client.post(url)
        publication.refresh_from_db()
        self.assertEqual(publication.status, "draft")

    def test_delete_publication(self):
        publication = self.make_publication()
        response = self.client.post(reverse("dashboard:publication_delete", args=[publication.pk]), follow=True)
        self.assertContains(response, "was deleted")
        self.assertFalse(Publication.objects.filter(pk=publication.pk).exists())

    def test_delete_confirmation_page_does_not_delete(self):
        publication = self.make_publication()
        response = self.client.get(reverse("dashboard:publication_delete", args=[publication.pk]))
        self.assertContains(response, "Delete this publication?")
        self.assertTrue(Publication.objects.filter(pk=publication.pk).exists())

    def test_missing_publication_returns_404(self):
        self.assertEqual(self.client.get(reverse("dashboard:publication_update", args=[9999])).status_code, 404)

    def test_list_search_and_filters(self):
        self.make_publication("Alpha guide", status="published", published_at=timezone.now())
        self.make_publication("Beta notes", kind="paper")
        response = self.client.get(reverse("dashboard:publication_list"), {"q": "alpha"})
        self.assertContains(response, "Alpha guide")
        self.assertNotContains(response, "Beta notes")
        response = self.client.get(reverse("dashboard:publication_list"), {"status": "draft"})
        self.assertContains(response, "Beta notes")
        self.assertNotContains(response, "Alpha guide")
        response = self.client.get(reverse("dashboard:publication_list"), {"kind": "paper"})
        self.assertContains(response, "Beta notes")
        response = self.client.get(
            reverse("dashboard:publication_list"), {"category": str(self.category.pk)}
        )
        self.assertContains(response, "Alpha guide")

    def test_list_pagination(self):
        for index in range(20):
            self.make_publication(f"Item {index:02d}")
        first = self.client.get(reverse("dashboard:publication_list"))
        self.assertEqual(len(first.context["items"]), 15)
        second = self.client.get(reverse("dashboard:publication_list"), {"page": 2})
        self.assertEqual(len(second.context["items"]), 5)

    def test_dashboard_counts(self):
        self.make_publication("Live", status="published", published_at=timezone.now() - timedelta(hours=1))
        self.make_publication("Draft")
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.context["published_count"], 1)
        self.assertEqual(response.context["draft_count"], 1)


class PageManagementTests(DashboardBase):
    def setUp(self):
        self.login_staff()

    def test_create_page(self):
        response = self.client.post(
            reverse("dashboard:page_create"),
            {"title": "About us", "slug": "", "content": "Hello", "meta_description": "", "is_published": "on", "menu_order": 0},
            follow=True,
        )
        self.assertContains(response, "“About us” was created.")
        self.assertEqual(Page.objects.get(title="About us").slug, "about-us")

    def test_page_content_is_required(self):
        response = self.client.post(reverse("dashboard:page_create"), {"title": "Empty", "menu_order": 0})
        self.assertContains(response, "This field is required.")

    def test_update_and_delete_page(self):
        page = Page.objects.create(title="Contact", content="Old")
        self.client.post(
            reverse("dashboard:page_update", args=[page.pk]),
            {"title": "Contact", "slug": page.slug, "content": "New", "meta_description": "", "is_published": "on", "menu_order": 0},
        )
        page.refresh_from_db()
        self.assertEqual(page.content, "New")
        self.client.post(reverse("dashboard:page_delete", args=[page.pk]))
        self.assertFalse(Page.objects.filter(pk=page.pk).exists())
