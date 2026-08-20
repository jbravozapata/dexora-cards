from django.urls import path
from . import views

app_name = "catalog"
urlpatterns = [
    path("pokemon/", views.species_list, name="species-list"),
    path("pokemon/<slug:slug>/", views.species_detail, name="species-detail"),
    path("cartas/<slug:slug>/", views.card_detail, name="card-detail"),
    path("cartas/<slug:slug>/imagen/", views.card_image_upload, name="card-image-upload"),
]
