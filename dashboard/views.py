from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from publications.models import Category, Page, Publication

from .forms import CategoryForm, PageForm, PublicationForm, StaffAuthenticationForm
from .mixins import StaffRequiredMixin


class LoginView(auth_views.LoginView):
    template_name = "dashboard/login.html"
    authentication_form = StaffAuthenticationForm
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    """POST-only logout (Django's default)."""


class DashboardHomeView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"
    section = "index"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "section": self.section,
                "published_count": Publication.objects.published().count(),
                "draft_count": Publication.objects.filter(status="draft").count(),
                "category_count": Category.objects.count(),
                "page_count": Page.objects.count(),
                "recent": Publication.objects.select_related("category").order_by(
                    "-updated_at"
                )[:6],
            }
        )
        return context


# --- Shared building blocks --------------------------------------------------
class ManageListView(StaffRequiredMixin, ListView):
    paginate_by = 15
    context_object_name = "items"
    section = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["section"] = self.section
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()
        context["q"] = self.request.GET.get("q", "").strip()
        return context


class ManageFormMixin(StaffRequiredMixin):
    template_name = "dashboard/form.html"
    heading = ""
    cancel_url = None
    multipart = False
    section = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "section": self.section,
                "heading": self.heading,
                "cancel_url": self.cancel_url,
                "multipart": self.multipart,
            }
        )
        return context


class ManageDeleteView(StaffRequiredMixin, DeleteView):
    template_name = "dashboard/confirm_delete.html"
    noun = "item"
    protected_message = ""
    section = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["section"] = self.section
        context["noun"] = self.noun
        context["cancel_url"] = self.success_url
        return context

    def form_valid(self, form):
        label = str(self.object)
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(
                self.request,
                self.protected_message
                or f"“{label}” can’t be deleted because other items still use it.",
            )
        else:
            messages.success(self.request, f"“{label}” was deleted.")
        return redirect(self.success_url)


# --- Publications ------------------------------------------------------------
class PublicationListView(ManageListView):
    section = "publications"
    model = Publication
    template_name = "dashboard/publication_list.html"

    def get_queryset(self):
        queryset = Publication.objects.select_related("category").order_by("-updated_at")
        params = self.request.GET
        query = params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(authors__icontains=query)
            )
        status = params.get("status", "")
        if status in Publication.Status.values:
            queryset = queryset.filter(status=status)
        kind = params.get("kind", "")
        if kind in Publication.Kind.values:
            queryset = queryset.filter(kind=kind)
        category = params.get("category", "")
        if category.isdigit():
            queryset = queryset.filter(category_id=int(category))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "status_choices": Publication.Status.choices,
                "kind_choices": Publication.Kind.choices,
                "categories": Category.objects.all(),
                "selected_status": self.request.GET.get("status", ""),
                "selected_kind": self.request.GET.get("kind", ""),
                "selected_category": self.request.GET.get("category", ""),
            }
        )
        return context


class PublicationCreateView(ManageFormMixin, SuccessMessageMixin, CreateView):
    section = "publications"
    model = Publication
    form_class = PublicationForm
    heading = "New publication"
    multipart = True
    cancel_url = reverse_lazy("dashboard:publication_list")
    success_url = reverse_lazy("dashboard:publication_list")
    success_message = "“%(title)s” was created."


class PublicationUpdateView(ManageFormMixin, SuccessMessageMixin, UpdateView):
    section = "publications"
    model = Publication
    form_class = PublicationForm
    heading = "Edit publication"
    multipart = True
    cancel_url = reverse_lazy("dashboard:publication_list")
    success_url = reverse_lazy("dashboard:publication_list")
    success_message = "“%(title)s” was saved."


class PublicationDeleteView(ManageDeleteView):
    section = "publications"
    model = Publication
    noun = "publication"
    success_url = reverse_lazy("dashboard:publication_list")


class PublicationToggleView(StaffRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        publication = get_object_or_404(Publication, pk=pk)
        if publication.status == Publication.Status.PUBLISHED:
            publication.status = Publication.Status.DRAFT
            messages.success(request, f"“{publication}” was moved back to drafts.")
        else:
            publication.status = Publication.Status.PUBLISHED
            messages.success(request, f"“{publication}” was published.")
        publication.save()
        return redirect("dashboard:publication_list")


# --- Categories --------------------------------------------------------------
class CategoryListView(ManageListView):
    section = "categories"
    model = Category
    template_name = "dashboard/category_list.html"

    def get_queryset(self):
        queryset = Category.objects.annotate(total=Count("publications")).order_by("name")
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(name__icontains=query)
        return queryset


class CategoryCreateView(ManageFormMixin, SuccessMessageMixin, CreateView):
    section = "categories"
    model = Category
    form_class = CategoryForm
    heading = "New category"
    cancel_url = reverse_lazy("dashboard:category_list")
    success_url = reverse_lazy("dashboard:category_list")
    success_message = "“%(name)s” was created."


class CategoryUpdateView(ManageFormMixin, SuccessMessageMixin, UpdateView):
    section = "categories"
    model = Category
    form_class = CategoryForm
    heading = "Edit category"
    cancel_url = reverse_lazy("dashboard:category_list")
    success_url = reverse_lazy("dashboard:category_list")
    success_message = "“%(name)s” was saved."


class CategoryDeleteView(ManageDeleteView):
    section = "categories"
    model = Category
    noun = "category"
    success_url = reverse_lazy("dashboard:category_list")
    protected_message = (
        "This category can’t be deleted while publications use it. "
        "Move or delete those publications first."
    )


# --- Pages -------------------------------------------------------------------
class PageListView(ManageListView):
    section = "pages"
    model = Page
    template_name = "dashboard/page_list.html"

    def get_queryset(self):
        queryset = Page.objects.all()
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(title__icontains=query)
        return queryset


class PageCreateView(ManageFormMixin, SuccessMessageMixin, CreateView):
    section = "pages"
    model = Page
    form_class = PageForm
    heading = "New page"
    cancel_url = reverse_lazy("dashboard:page_list")
    success_url = reverse_lazy("dashboard:page_list")
    success_message = "“%(title)s” was created."


class PageUpdateView(ManageFormMixin, SuccessMessageMixin, UpdateView):
    section = "pages"
    model = Page
    form_class = PageForm
    heading = "Edit page"
    cancel_url = reverse_lazy("dashboard:page_list")
    success_url = reverse_lazy("dashboard:page_list")
    success_message = "“%(title)s” was saved."


class PageDeleteView(ManageDeleteView):
    section = "pages"
    model = Page
    noun = "page"
    success_url = reverse_lazy("dashboard:page_list")
