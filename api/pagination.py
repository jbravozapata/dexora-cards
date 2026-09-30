from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50


class PersonalPokedexPagination(PageNumberPagination):
    """The mobile Pokédex always exposes one 4×4 page."""

    page_size = 16
