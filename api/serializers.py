from rest_framework import serializers

from catalog.models import PokemonSpecies, TCGCard
from collections_app.models import UserCollectionItem
from pokedex_app.models import UserPokemon
from users.models import UserProfile
from wishlist_app.models import WishlistItem


def absolute_url(request, value):
    if not value:
        return ""
    return request.build_absolute_uri(value) if request else value


class SpeciesSerializer(serializers.ModelSerializer):
    types = serializers.ListField(read_only=True)
    artwork = serializers.SerializerMethodField()
    card_count = serializers.IntegerField(read_only=True, default=0)
    is_owned = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = PokemonSpecies
        fields = (
            "id", "national_dex_number", "api_name", "display_name", "slug",
            "generation", "types", "description", "artwork", "card_count", "is_owned",
        )

    def get_artwork(self, obj):
        return absolute_url(self.context.get("request"), obj.effective_artwork)


class CardSerializer(serializers.ModelSerializer):
    set_name = serializers.CharField(source="set.name", read_only=True)
    set_series = serializers.CharField(source="set.series", read_only=True)
    release_date = serializers.DateField(source="set.release_date", read_only=True)
    image = serializers.SerializerMethodField()
    species = SpeciesSerializer(many=True, read_only=True)
    is_wished = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = TCGCard
        fields = (
            "id", "external_id", "name", "slug", "number", "rarity", "artist",
            "supertype", "subtypes", "types", "hp", "set_name", "set_series",
            "release_date", "image", "species", "is_wished",
        )

    def get_image(self, obj):
        return absolute_url(self.context.get("request"), obj.effective_image)


class CollectionItemSerializer(serializers.ModelSerializer):
    card = CardSerializer(read_only=True)

    class Meta:
        model = UserCollectionItem
        fields = ("id", "card", "quantity", "variant", "condition", "notes", "updated_at")


class WishlistItemSerializer(serializers.ModelSerializer):
    card = CardSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ("id", "card", "created_at")


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    name = serializers.CharField(read_only=True)
    avatar = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = (
            "username", "name", "collector_title", "motto", "bio", "location",
            "collecting_since", "favorite_type", "accent", "avatar", "cover_image",
        )

    def get_avatar(self, obj):
        value = obj.avatar.url if obj.avatar else ""
        return absolute_url(self.context.get("request"), value)

    def get_cover_image(self, obj):
        value = obj.cover_image.url if obj.cover_image else ""
        return absolute_url(self.context.get("request"), value)
