class CardItem {
  const CardItem({
    required this.id,
    required this.name,
    required this.setName,
    required this.number,
    required this.image,
    required this.isWished,
  });
  final int id;
  final String name;
  final String setName;
  final String number;
  final String image;
  final bool isWished;

  factory CardItem.fromJson(Map<String, dynamic> json) => CardItem(
    id: json['id'] as int,
    name: json['name'] as String? ?? '',
    setName: json['set_name'] as String? ?? '',
    number: json['number'] as String? ?? '',
    image: json['image'] as String? ?? '',
    isWished: json['is_wished'] as bool? ?? false,
  );

  CardItem copyWith({bool? isWished}) => CardItem(
    id: id,
    name: name,
    setName: setName,
    number: number,
    image: image,
    isWished: isWished ?? this.isWished,
  );
}
