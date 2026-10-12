from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardHomeView.as_view(), name="index"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    # Publications
    path("publications/", views.PublicationListView.as_view(), name="publication_list"),
    path("publications/new/", views.PublicationCreateView.as_view(), name="publication_create"),
    path("publications/<int:pk>/edit/", views.PublicationUpdateView.as_view(), name="publication_update"),
    path("publications/<int:pk>/delete/", views.PublicationDeleteView.as_view(), name="publication_delete"),
    path("publications/<int:pk>/toggle/", views.PublicationToggleView.as_view(), name="publication_toggle"),
    # Categories
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("categories/new/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_update"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),
    # Pages
    path("pages/", views.PageListView.as_view(), name="page_list"),
    path("pages/new/", views.PageCreateView.as_view(), name="page_create"),
    path("pages/<int:pk>/edit/", views.PageUpdateView.as_view(), name="page_update"),
    path("pages/<int:pk>/delete/", views.PageDeleteView.as_view(), name="page_delete"),
]
