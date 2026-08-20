from django.urls import path

from . import views

app_name = "wishlist"

urlpatterns = [
    path("", views.wishlist_list, name="list"),
    path("carta/<slug:card_slug>/alternar/", views.toggle_item, name="toggle"),
]
