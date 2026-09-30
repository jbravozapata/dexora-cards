from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("species/", views.SpeciesListView.as_view(), name="species-list"),
    path("species/<slug:slug>/", views.SpeciesDetailView.as_view(), name="species-detail"),
    path("cards/", views.CardListView.as_view(), name="card-list"),
    path("cards/<slug:slug>/", views.CardDetailView.as_view(), name="card-detail"),
    path("collection/", views.CollectionView.as_view(), name="collection"),
    path("collection/<int:pk>/", views.CollectionItemView.as_view(), name="collection-item"),
    path("wishlist/", views.WishlistView.as_view(), name="wishlist"),
    path("wishlist/toggle/", views.WishlistToggleView.as_view(), name="wishlist-toggle"),
    path("my-pokemon/", views.PersonalPokedexView.as_view(), name="my-pokemon"),
    path("my-pokemon/<int:species_id>/toggle/", views.PersonalPokedexToggleView.as_view(), name="my-pokemon-toggle"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
]
