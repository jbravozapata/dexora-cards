import 'package:dexora_mobile/core/theme.dart';
import 'package:dexora_mobile/models/species.dart';
import 'package:dexora_mobile/widgets/common.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Species parses ownership and catalog fields', () {
    final species = Species.fromJson({
      'id': 25,
      'national_dex_number': 25,
      'display_name': 'Pikachu',
      'slug': '25-pikachu',
      'generation': 'Generación I',
      'types': ['electric'],
      'artwork': 'https://example.com/pikachu.png',
      'card_count': 100,
      'is_owned': true,
    });

    expect(species.name, 'Pikachu');
    expect(species.isOwned, isTrue);
    expect(species.copyWith(isOwned: false).isOwned, isFalse);
  });

  testWidgets('Dexora header keeps title and subtitle accessible', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: buildDexoraTheme(),
        home: const Scaffold(
          body: DexoraHeader(
            title: 'Mis 1025 Pokémon',
            subtitle: 'Pokédex personal',
          ),
        ),
      ),
    );

    expect(find.text('Mis 1025 Pokémon'), findsOneWidget);
    expect(find.text('Pokédex personal'), findsOneWidget);
  });
}
