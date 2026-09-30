import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../core/api_client.dart';
import '../core/theme.dart';
import '../models/species.dart';
import '../widgets/common.dart';

class PersonalPokedexScreen extends StatefulWidget {
  const PersonalPokedexScreen({super.key, required this.api});
  final ApiClient api;

  @override
  State<PersonalPokedexScreen> createState() => _PersonalPokedexScreenState();
}

class _PersonalPokedexScreenState extends State<PersonalPokedexScreen> {
  final search = TextEditingController();
  List<Species> species = const [];
  Map<String, dynamic> summary = const {
    'owned': 0,
    'missing': 0,
    'total': 1025,
    'progress': 0,
  };
  int page = 1;
  int totalResults = 0;
  String stateFilter = 'all';
  bool loading = true;
  String? error;

  int get pages => math.max(1, (totalResults / 16).ceil());

  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    search.dispose();
    super.dispose();
  }

  Future<void> load({int? targetPage}) async {
    setState(() {
      loading = true;
      error = null;
      if (targetPage != null) page = targetPage;
    });
    try {
      final data =
          await widget.api.get(
                '/my-pokemon/',
                query: {
                  'page': '$page',
                  'q': search.text.trim(),
                  'state': stateFilter,
                },
              )
              as Map<String, dynamic>;
      if (!mounted) return;
      setState(() {
        species = (data['results'] as List)
            .map((item) => Species.fromJson(item as Map<String, dynamic>))
            .toList();
        summary = data['summary'] as Map<String, dynamic>? ?? summary;
        totalResults = data['count'] as int? ?? species.length;
        loading = false;
      });
    } catch (exception) {
      if (mounted) {
        setState(() {
          error = exception.toString();
          loading = false;
        });
      }
    }
  }

  Future<void> toggle(Species pokemon) async {
    final index = species.indexWhere((item) => item.id == pokemon.id);
    if (index < 0) return;
    final desired = !pokemon.isOwned;
    setState(
      () =>
          species = [...species]..[index] = pokemon.copyWith(isOwned: desired),
    );
    try {
      final data =
          await widget.api.post(
                '/my-pokemon/${pokemon.id}/toggle/',
                body: {'owned': desired},
              )
              as Map<String, dynamic>;
      if (!mounted) return;
      setState(
        () => summary = {
          ...summary,
          ...(data['summary'] as Map<String, dynamic>),
        },
      );
      if (stateFilter != 'all') await load(targetPage: page);
    } catch (exception) {
      if (!mounted) return;
      setState(() => species = [...species]..[index] = pokemon);
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(exception.toString())));
    }
  }

  @override
  Widget build(BuildContext context) {
    final owned = summary['owned'] as int? ?? 0;
    final total = summary['total'] as int? ?? 1025;
    final progress = total == 0 ? 0.0 : owned / total;
    return SafeArea(
      child: Column(
        children: [
          const DexoraHeader(
            title: 'Mis 1025 Pokémon',
            subtitle: 'Tu Pokédex personal, independiente de las cartas TCG.',
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: DexoraColors.navySoft,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: DexoraColors.line),
              ),
              child: Column(
                children: [
                  Row(
                    children: [
                      Text(
                        '$owned',
                        style: const TextStyle(
                          color: DexoraColors.cyan,
                          fontWeight: FontWeight.w900,
                          fontSize: 24,
                        ),
                      ),
                      Text(
                        ' / $total obtenidos',
                        style: const TextStyle(
                          color: DexoraColors.muted,
                          fontSize: 12,
                        ),
                      ),
                      const Spacer(),
                      Text(
                        '${(progress * 100).toStringAsFixed(1)}%',
                        style: const TextStyle(
                          color: DexoraColors.gold,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: LinearProgressIndicator(
                      value: progress,
                      minHeight: 5,
                      backgroundColor: DexoraColors.line,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 10),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: search,
                    textInputAction: TextInputAction.search,
                    onSubmitted: (_) => load(targetPage: 1),
                    style: const TextStyle(fontSize: 13),
                    decoration: const InputDecoration(
                      hintText: 'Nombre o #025',
                      prefixIcon: Icon(Icons.search),
                      isDense: true,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                PopupMenuButton<String>(
                  initialValue: stateFilter,
                  tooltip: 'Filtrar estado',
                  icon: const Icon(Icons.tune),
                  onSelected: (value) {
                    stateFilter = value;
                    load(targetPage: 1);
                  },
                  itemBuilder: (_) => const [
                    PopupMenuItem(value: 'all', child: Text('Todos')),
                    PopupMenuItem(value: 'owned', child: Text('Obtenidos')),
                    PopupMenuItem(value: 'missing', child: Text('Pendientes')),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),
          Expanded(
            child: loading
                ? const Center(child: CircularProgressIndicator())
                : error != null
                ? ErrorPane(message: error!, retry: load)
                : species.isEmpty
                ? const Center(
                    child: Text(
                      'No encontramos Pokémon para este filtro.',
                      style: TextStyle(color: DexoraColors.muted),
                    ),
                  )
                : Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 10),
                    child: GridView.builder(
                      itemCount: species.length,
                      gridDelegate:
                          const SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: 4,
                            mainAxisSpacing: 7,
                            crossAxisSpacing: 7,
                            childAspectRatio: .68,
                          ),
                      itemBuilder: (_, index) => _PokemonCell(
                        pokemon: species[index],
                        onTap: () => toggle(species[index]),
                      ),
                    ),
                  ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 7, 16, 10),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                IconButton(
                  onPressed: page > 1 && !loading
                      ? () => load(targetPage: page - 1)
                      : null,
                  icon: const Icon(Icons.chevron_left),
                  tooltip: 'Página anterior',
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 18,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    border: Border.all(color: DexoraColors.line),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    '$page / $pages',
                    style: const TextStyle(
                      fontWeight: FontWeight.w800,
                      fontSize: 12,
                    ),
                  ),
                ),
                IconButton(
                  onPressed: page < pages && !loading
                      ? () => load(targetPage: page + 1)
                      : null,
                  icon: const Icon(Icons.chevron_right),
                  tooltip: 'Página siguiente',
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _PokemonCell extends StatelessWidget {
  const _PokemonCell({required this.pokemon, required this.onTap});
  final Species pokemon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Semantics(
    button: true,
    label: '${pokemon.name}, ${pokemon.isOwned ? 'obtenido' : 'pendiente'}',
    child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.fromLTRB(5, 5, 5, 7),
        decoration: BoxDecoration(
          color: pokemon.isOwned
              ? DexoraColors.cyan.withValues(alpha: .09)
              : DexoraColors.navySoft,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: pokemon.isOwned ? DexoraColors.cyan : DexoraColors.line,
            width: pokemon.isOwned ? 1.5 : 1,
          ),
        ),
        child: Column(
          children: [
            Row(
              children: [
                Text(
                  '#${pokemon.number.toString().padLeft(4, '0')}',
                  style: TextStyle(
                    color: pokemon.isOwned
                        ? DexoraColors.cyan
                        : DexoraColors.muted,
                    fontSize: 8,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const Spacer(),
                Icon(
                  pokemon.isOwned
                      ? Icons.check_circle
                      : Icons.radio_button_unchecked,
                  size: 14,
                  color: pokemon.isOwned
                      ? DexoraColors.cyan
                      : DexoraColors.muted,
                ),
              ],
            ),
            Expanded(child: NetworkArtwork(url: pokemon.artwork)),
            Text(
              pokemon.name,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w800),
            ),
          ],
        ),
      ),
    ),
  );
}
