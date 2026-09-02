from django.urls import path
from . import views

app_name = "collection"
urlpatterns = [
    path("", views.collection_list, name="list"),
    path("rapido/carta/<slug:card_slug>/", views.card_quick_add, name="card-quick-add"),
    path("rapido/<slug:species_slug>/", views.quick_picker, name="quick-picker"),
    path("rapido/<slug:species_slug>/<slug:card_slug>/", views.quick_add, name="quick-add"),
    path("carta/<slug:card_slug>/", views.item_edit, name="item-edit"),
    path("item/<int:pk>/eliminar/", views.item_delete, name="item-delete"),
    path("eliminar-seleccion/", views.bulk_delete, name="bulk-delete"),
]
