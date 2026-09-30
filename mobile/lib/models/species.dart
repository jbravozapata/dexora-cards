class Species {
  const Species({
    required this.id,
    required this.number,
    required this.name,
    required this.slug,
    required this.generation,
    required this.types,
    required this.artwork,
    required this.cardCount,
    required this.isOwned,
  });

  final int id;
  final int number;
  final String name;
  final String slug;
  final String generation;
  final List<String> types;
  final String artwork;
  final int cardCount;
  final bool isOwned;

  factory Species.fromJson(Map<String, dynamic> json) => Species(
    id: json['id'] as int,
    number: json['national_dex_number'] as int,
    name: json['display_name'] as String? ?? '',
    slug: json['slug'] as String? ?? '',
    generation: json['generation'] as String? ?? '',
    types: (json['types'] as List? ?? const [])
        .map((value) => value.toString())
        .toList(),
    artwork: json['artwork'] as String? ?? '',
    cardCount: json['card_count'] as int? ?? 0,
    isOwned: json['is_owned'] as bool? ?? false,
  );

  Species copyWith({bool? isOwned}) => Species(
    id: id,
    number: number,
    name: name,
    slug: slug,
    generation: generation,
    types: types,
    artwork: artwork,
    cardCount: cardCount,
    isOwned: isOwned ?? this.isOwned,
  );
}
