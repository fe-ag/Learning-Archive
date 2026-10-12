from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.text import Truncator
from django.views.generic import DetailView, ListView, TemplateView

from .models import Category, Page, Publication

SORT_OPTIONS = {
    "newest": ("-published_at", "-id"),
    "oldest": ("published_at", "id"),
    "title": ("title", "id"),
}
SORT_LABELS = [("newest", "Newest first"), ("oldest", "Oldest first"), ("title", "Title A–Z")]


class HomeView(TemplateView):
    template_name = "publications/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        published = Publication.objects.published().select_related("category")
        context["featured"] = published.filter(is_featured=True)[:3]
        context["latest"] = published[:6]
        context["categories"] = Category.objects.with_published_count().filter(
            published_count__gt=0
        )
        return context


class PublicationListView(ListView):
    """Archive listing with search, filters, sorting and pagination.

    Also serves ``/category/<slug>/`` where the category is fixed by the URL.
    """

    template_name = "publications/publication_list.html"
    context_object_name = "publications"
    paginate_by = 12

    def get_category(self):
        if not hasattr(self, "_category"):
            slug = self.kwargs.get("slug")
            self._category = get_object_or_404(Category, slug=slug) if slug else None
        return self._category

    def get_queryset(self):
        queryset = Publication.objects.published().select_related("category")
        params = self.request.GET

        category = self.get_category()
        if category:
            queryset = queryset.filter(category=category)
        else:
            category_slug = params.get("category", "").strip()
            if category_slug:
                queryset = queryset.filter(category__slug=category_slug)

        kind = params.get("kind", "").strip()
        if kind in Publication.Kind.values:
            queryset = queryset.filter(kind=kind)

        query = params.get("q", "").strip()[:100]
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(authors__icontains=query)
                | Q(body__icontains=query)
            )

        sort = params.get("sort", "newest")
        return queryset.order_by(*SORT_OPTIONS.get(sort, SORT_OPTIONS["newest"]))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET
        category = self.get_category()
        sort = params.get("sort", "newest")
        if sort not in SORT_OPTIONS:
            sort = "newest"

        query_params = params.copy()
        query_params.pop("page", None)

        context.update(
            {
                "category": category,
                "categories": Category.objects.with_published_count().filter(
                    published_count__gt=0
                ),
                "kinds": Publication.Kind.choices,
                "sorts": SORT_LABELS,
                "q": params.get("q", "").strip()[:100],
                "selected_kind": params.get("kind", ""),
                "selected_category": params.get("category", ""),
                "selected_sort": sort,
                "querystring": query_params.urlencode(),
                "meta_title": category.name if category else "Browse the archive",
                "meta_description": (
                    Truncator(category.description).chars(160)
                    if category and category.description
                    else "Browse articles, papers and learning resources."
                ),
            }
        )
        return context


class PublicationDetailView(DetailView):
    template_name = "publications/publication_detail.html"
    context_object_name = "publication"

    def get_queryset(self):
        return Publication.objects.published().select_related("category")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        publication = self.object
        context["related"] = (
            Publication.objects.published()
            .filter(category=publication.category)
            .exclude(pk=publication.pk)
            .select_related("category")[:3]
        )
        context["meta_title"] = publication.meta_title or publication.title
        context["meta_description"] = publication.meta_description or Truncator(
            publication.summary
        ).chars(160)
        context["og_type"] = "article"
        return context


class PageDetailView(DetailView):
    template_name = "publications/page_detail.html"
    context_object_name = "page"

    def get_queryset(self):
        return Page.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meta_title"] = self.object.title
        context["meta_description"] = self.object.meta_description
        return context
