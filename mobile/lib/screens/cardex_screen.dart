import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../core/api_client.dart';
import '../core/theme.dart';
import '../models/species.dart';
import '../widgets/common.dart';
import 'species_cards_screen.dart';

class CardexScreen extends StatefulWidget {
  const CardexScreen({super.key, required this.api});
  final ApiClient api;

  @override
  State<CardexScreen> createState() => _CardexScreenState();
}

class _CardexScreenState extends State<CardexScreen> {
  final search = TextEditingController();
  List<Species> items = const [];
  int page = 1;
  int count = 0;
  bool loading = true;
  String? error;
  int get pages => math.max(1, (count / 20).ceil());

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
                '/species/',
                query: {'page': '$page', 'q': search.text.trim()},
              )
              as Map<String, dynamic>;
      if (!mounted) return;
      setState(() {
        items = (data['results'] as List)
            .map((item) => Species.fromJson(item as Map<String, dynamic>))
            .toList();
        count = data['count'] as int? ?? 0;
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

  @override
  Widget build(BuildContext context) => SafeArea(
    child: Column(
      children: [
        DexoraHeader(title: 'Cardex', subtitle: '$count especies catalogadas'),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
          child: TextField(
            controller: search,
            onSubmitted: (_) => load(targetPage: 1),
            decoration: const InputDecoration(
              hintText: 'Busca por nombre o número',
              prefixIcon: Icon(Icons.search),
            ),
          ),
        ),
        Expanded(
          child: loading
              ? const Center(child: CircularProgressIndicator())
              : error != null
              ? ErrorPane(message: error!, retry: load)
              : GridView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 14),
                  itemCount: items.length,
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    childAspectRatio: 1.08,
                    crossAxisSpacing: 10,
                    mainAxisSpacing: 10,
                  ),
                  itemBuilder: (_, index) => _SpeciesCard(
                    species: items[index],
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => SpeciesCardsScreen(
                          api: widget.api,
                          species: items[index],
                        ),
                      ),
                    ),
                  ),
                ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              IconButton(
                onPressed: page > 1 ? () => load(targetPage: page - 1) : null,
                icon: const Icon(Icons.chevron_left),
              ),
              Text(
                '$page / $pages',
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
              IconButton(
                onPressed: page < pages
                    ? () => load(targetPage: page + 1)
                    : null,
                icon: const Icon(Icons.chevron_right),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}

class _SpeciesCard extends StatelessWidget {
  const _SpeciesCard({required this.species, required this.onTap});
  final Species species;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => InkWell(
    onTap: onTap,
    borderRadius: BorderRadius.circular(14),
    child: Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: species.isOwned ? DexoraColors.cyan : DexoraColors.line,
        ),
        color: DexoraColors.navySoft,
      ),
      child: Stack(
        children: [
          Positioned(
            right: 8,
            top: 7,
            child: Text(
              '#${species.number.toString().padLeft(4, '0')}',
              style: const TextStyle(
                color: DexoraColors.cyan,
                fontSize: 10,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Center(child: NetworkArtwork(url: species.artwork)),
                ),
                Text(
                  species.name,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '${species.generation} · ${species.cardCount} cartas',
                  maxLines: 1,
                  style: const TextStyle(
                    color: DexoraColors.muted,
                    fontSize: 9,
                  ),
                ),
              ],
            ),
          ),
          if (species.isOwned)
            const Positioned(
              left: 8,
              top: 7,
              child: Icon(
                Icons.check_circle,
                color: DexoraColors.cyan,
                size: 16,
              ),
            ),
        ],
      ),
    ),
  );
}
