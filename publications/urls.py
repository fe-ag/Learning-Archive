from django.urls import path

from . import views

app_name = "publications"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("publications/", views.PublicationListView.as_view(), name="list"),
    path("publications/<slug:slug>/", views.PublicationDetailView.as_view(), name="detail"),
    path("category/<slug:slug>/", views.PublicationListView.as_view(), name="category"),
    path("page/<slug:slug>/", views.PageDetailView.as_view(), name="page"),
]
