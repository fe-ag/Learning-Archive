from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from publications.models import Category, Page, Publication


class StaffAuthenticationForm(AuthenticationForm):
    """Login form that only lets staff accounts into the management area."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise ValidationError(
                "This account does not have access to the management area.",
                code="not_staff",
            )


class StyledModelForm(forms.ModelForm):
    """Adds consistent CSS classes to every widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "checkbox" if isinstance(field.widget, forms.CheckboxInput) else "input"
            field.widget.attrs["class"] = css


class CategoryForm(StyledModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}
        help_texts = {
            "slug": "Used in the address of the category page. Leave blank to generate it from the name.",
            "description": "Shown at the top of the category page and used for search engines.",
        }


class PublicationForm(StyledModelForm):
    class Meta:
        model = Publication
        fields = [
            "title",
            "slug",
            "kind",
            "category",
            "authors",
            "summary",
            "body",
            "attachment",
            "external_url",
            "meta_title",
            "meta_description",
            "status",
            "published_at",
            "is_featured",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "body": forms.Textarea(attrs={"rows": 14}),
            "published_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }
        help_texts = {
            "slug": "Leave blank to generate it from the title.",
            "authors": "Separate several authors with commas.",
            "summary": "Up to 600 characters. Shown in lists and search results.",
            "body": "Plain text. Blank lines start a new paragraph.",
            "attachment": "PDF, Word, PowerPoint, Excel, EPUB, text or ZIP. Maximum size is set by MAX_UPLOAD_MB.",
            "external_url": "Optional link to the original source (http or https).",
            "meta_title": "Optional title for search engines (up to 70 characters).",
            "meta_description": "Optional description for search engines (up to 160 characters).",
            "published_at": "Leave blank to publish immediately. A future date schedules the publication.",
            "is_featured": "Featured publications appear on the home page.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["published_at"].input_formats = [
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ]

    def clean_external_url(self):
        url = self.cleaned_data.get("external_url", "")
        if url and not url.lower().startswith(("http://", "https://")):
            raise ValidationError("Enter a link that starts with http:// or https://.")
        return url

    def clean(self):
        cleaned = super().clean()
        if not (
            cleaned.get("body")
            or cleaned.get("attachment")
            or cleaned.get("external_url")
        ):
            raise ValidationError(
                "Add body text, upload a file, or provide an external link."
            )
        return cleaned


class PageForm(StyledModelForm):
    class Meta:
        model = Page
        fields = [
            "title",
            "slug",
            "content",
            "meta_description",
            "is_published",
            "show_in_menu",
            "menu_order",
        ]
        widgets = {"content": forms.Textarea(attrs={"rows": 14})}
        help_texts = {
            "slug": "Leave blank to generate it from the title.",
            "content": "Plain text. Blank lines start a new paragraph.",
            "meta_description": "Optional description for search engines (up to 160 characters).",
            "show_in_menu": "Show a link to this page in the site header and footer.",
            "menu_order": "Lower numbers appear first.",
        }
