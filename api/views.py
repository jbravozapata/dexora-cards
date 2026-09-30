from django.contrib.auth import authenticate
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import PokemonSpecies, TCGCard
from collections_app.models import UserCollectionItem
from pokedex_app.models import UserPokemon
from users.models import UserProfile
from wishlist_app.models import WishlistItem

from .pagination import PersonalPokedexPagination, StandardPagination
from .serializers import (
    CardSerializer,
    CollectionItemSerializer,
    ProfileSerializer,
    SpeciesSerializer,
    WishlistItemSerializer,
)


def species_queryset(user):
    owned = UserPokemon.objects.filter(user=user, species_id=OuterRef("pk"))
    return (
        PokemonSpecies.objects.filter(is_active=True)
        .annotate(
            card_count=Count("cards", filter=Q(cards__is_visible=True), distinct=True),
            is_owned=Exists(owned),
        )
        .order_by("national_dex_number")
    )


def cards_queryset(user):
    wished = WishlistItem.objects.filter(user=user, card_id=OuterRef("pk"))
    return (
        TCGCard.objects.filter(is_visible=True)
        .select_related("set")
        .prefetch_related("species")
        .annotate(is_wished=Exists(wished))
        .order_by("-set__release_date", "name", "number")
    )


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        password = str(request.data.get("password", ""))
        user = authenticate(request=request, username=username, password=password)
        if user is None or not user.is_active:
            return Response(
                {"detail": "Usuario o contraseña incorrectos."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": {"id": user.pk, "username": user.username}})


class LogoutView(APIView):
    def post(self, request):
        if request.auth:
            request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DashboardView(APIView):
    def get(self, request):
        collection = UserCollectionItem.objects.filter(user=request.user)
        totals = collection.aggregate(cards=Count("card", distinct=True), copies=Sum("quantity"))
        total_species = PokemonSpecies.objects.filter(is_active=True).count()
        owned_species = UserPokemon.objects.filter(user=request.user, species__is_active=True).count()
        return Response({
            "species_total": total_species,
            "species_owned": owned_species,
            "species_progress": round((owned_species / total_species * 100), 1) if total_species else 0,
            "cards_different": totals["cards"] or 0,
            "cards_total": totals["copies"] or 0,
            "wishlist_total": WishlistItem.objects.filter(user=request.user).count(),
        })


class SpeciesListView(generics.ListAPIView):
    serializer_class = SpeciesSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = species_queryset(self.request.user)
        query = self.request.query_params.get("q", "").strip()
        if query:
            condition = Q(display_name__icontains=query) | Q(api_name__icontains=query)
            numeric = query.lstrip("#")
            if numeric.isdigit():
                condition |= Q(national_dex_number=int(numeric))
            queryset = queryset.filter(condition)
        generation = self.request.query_params.get("generation")
        pokemon_type = self.request.query_params.get("type")
        if generation:
            queryset = queryset.filter(generation=generation)
        if pokemon_type:
            queryset = queryset.filter(Q(primary_type=pokemon_type) | Q(secondary_type=pokemon_type))
        return queryset


class SpeciesDetailView(generics.RetrieveAPIView):
    serializer_class = SpeciesSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return species_queryset(self.request.user)


class CardListView(generics.ListAPIView):
    serializer_class = CardSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = cards_queryset(self.request.user)
        query = self.request.query_params.get("q", "").strip()
        species = self.request.query_params.get("species")
        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(set__name__icontains=query))
        if species:
            queryset = queryset.filter(species__slug=species)
        return queryset.distinct()


class CardDetailView(generics.RetrieveAPIView):
    serializer_class = CardSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return cards_queryset(self.request.user)


class CollectionView(APIView):
    pagination_class = StandardPagination

    def get(self, request):
        queryset = (
            UserCollectionItem.objects.filter(user=request.user, card__is_visible=True)
            .select_related("card", "card__set")
            .prefetch_related("card__species")
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(CollectionItemSerializer(page, many=True, context={"request": request}).data)

    def post(self, request):
        card = get_object_or_404(TCGCard, pk=request.data.get("card_id"), is_visible=True)
        variant = request.data.get("variant", UserCollectionItem.Variant.STANDARD)
        condition = request.data.get("condition", UserCollectionItem.Condition.NEAR_MINT)
        valid_variants = {choice for choice, _ in UserCollectionItem.Variant.choices}
        valid_conditions = {choice for choice, _ in UserCollectionItem.Condition.choices}
        if variant not in valid_variants or condition not in valid_conditions:
            return Response({"detail": "Variante o condición no válida."}, status=status.HTTP_400_BAD_REQUEST)
        requested_quantity = request.data.get("quantity")
        parsed_quantity = None
        if requested_quantity is not None:
            try:
                parsed_quantity = int(requested_quantity)
            except (TypeError, ValueError):
                return Response({"detail": "Cantidad no válida."}, status=status.HTTP_400_BAD_REQUEST)
            if not 1 <= parsed_quantity <= 999:
                return Response(
                    {"detail": "La cantidad debe estar entre 1 y 999."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        with transaction.atomic():
            item, created = UserCollectionItem.objects.select_for_update().get_or_create(
                user=request.user,
                card=card,
                variant=variant,
                condition=condition,
                defaults={"quantity": parsed_quantity or 1},
            )
            if not created:
                if parsed_quantity is None:
                    item.quantity += 1
                else:
                    item.quantity = parsed_quantity
                item.save(update_fields=["quantity", "updated_at"])
        return Response(
            CollectionItemSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CollectionItemView(APIView):
    def patch(self, request, pk):
        item = get_object_or_404(UserCollectionItem, pk=pk, user=request.user)
        try:
            quantity = int(request.data.get("quantity"))
        except (TypeError, ValueError):
            return Response({"detail": "Cantidad no válida."}, status=status.HTTP_400_BAD_REQUEST)
        if not 1 <= quantity <= 999:
            return Response({"detail": "La cantidad debe estar entre 1 y 999."}, status=status.HTTP_400_BAD_REQUEST)
        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])
        return Response(CollectionItemSerializer(item, context={"request": request}).data)

    def delete(self, request, pk):
        item = get_object_or_404(UserCollectionItem, pk=pk, user=request.user)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WishlistView(generics.ListAPIView):
    serializer_class = WishlistItemSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return (
            WishlistItem.objects.filter(user=self.request.user, card__is_visible=True)
            .select_related("card", "card__set")
            .prefetch_related("card__species")
        )


class WishlistToggleView(APIView):
    def post(self, request):
        card = get_object_or_404(TCGCard, pk=request.data.get("card_id"), is_visible=True)
        item, created = WishlistItem.objects.get_or_create(user=request.user, card=card)
        if not created:
            item.delete()
        return Response({"card_id": card.pk, "is_wished": created})


class PersonalPokedexView(generics.ListAPIView):
    serializer_class = SpeciesSerializer
    pagination_class = PersonalPokedexPagination

    def get_queryset(self):
        queryset = species_queryset(self.request.user)
        query = self.request.query_params.get("q", "").strip()
        state = self.request.query_params.get("state", "all")
        if query:
            condition = Q(display_name__icontains=query) | Q(api_name__icontains=query)
            if query.lstrip("#").isdigit():
                condition |= Q(national_dex_number=int(query.lstrip("#")))
            queryset = queryset.filter(condition)
        if state == "owned":
            queryset = queryset.filter(is_owned=True)
        elif state == "missing":
            queryset = queryset.filter(is_owned=False)
        return queryset

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        total = PokemonSpecies.objects.filter(is_active=True).count()
        owned = UserPokemon.objects.filter(user=self.request.user, species__is_active=True).count()
        response.data["summary"] = {
            "owned": owned,
            "missing": max(total - owned, 0),
            "total": total,
            "progress": round((owned / total * 100), 1) if total else 0,
            "page_size": 16,
        }
        return response


class PersonalPokedexToggleView(APIView):
    def post(self, request, species_id):
        pokemon = get_object_or_404(PokemonSpecies, pk=species_id, is_active=True)
        item = UserPokemon.objects.filter(user=request.user, species=pokemon).first()
        desired = request.data.get("owned")
        if desired not in (None, True, False):
            return Response({"detail": "El estado debe ser verdadero o falso."}, status=status.HTTP_400_BAD_REQUEST)
        should_own = (not bool(item)) if desired is None else bool(desired)
        if should_own and item is None:
            UserPokemon.objects.create(user=request.user, species=pokemon)
        elif not should_own and item is not None:
            item.delete()
        owned = UserPokemon.objects.filter(user=request.user, species__is_active=True).count()
        total = PokemonSpecies.objects.filter(is_active=True).count()
        return Response({
            "species_id": pokemon.pk,
            "is_owned": should_own,
            "summary": {"owned": owned, "missing": max(total - owned, 0), "total": total},
        })


class ProfileView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
