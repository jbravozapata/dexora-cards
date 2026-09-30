import 'package:flutter/material.dart';

import '../core/api_client.dart';
import '../core/theme.dart';
import '../models/card_item.dart';
import '../models/species.dart';
import '../widgets/common.dart';

class SpeciesCardsScreen extends StatefulWidget {
  const SpeciesCardsScreen({
    super.key,
    required this.api,
    required this.species,
  });
  final ApiClient api;
  final Species species;

  @override
  State<SpeciesCardsScreen> createState() => _SpeciesCardsScreenState();
}

class _SpeciesCardsScreenState extends State<SpeciesCardsScreen> {
  List<CardItem> cards = const [];
  bool loading = true;
  String? error;
  final Set<int> added = {};

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    try {
      final data =
          await widget.api.get(
                '/cards/',
                query: {'species': widget.species.slug, 'page_size': '50'},
              )
              as Map<String, dynamic>;
      if (mounted) {
        setState(() {
          cards = (data['results'] as List)
              .map((item) => CardItem.fromJson(item as Map<String, dynamic>))
              .toList();
          loading = false;
          error = null;
        });
      }
    } catch (exception) {
      if (mounted) {
        setState(() {
          error = exception.toString();
          loading = false;
        });
      }
    }
  }

  Future<void> addCard(CardItem card) async {
    try {
      await widget.api.post('/collection/', body: {'card_id': card.id});
      if (mounted) setState(() => added.add(card.id));
    } catch (exception) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(exception.toString())));
      }
    }
  }

  Future<void> toggleWish(CardItem card) async {
    final index = cards.indexWhere((item) => item.id == card.id);
    if (index < 0) return;
    final desired = !card.isWished;
    setState(
      () => cards = [...cards]..[index] = card.copyWith(isWished: desired),
    );
    try {
      await widget.api.post('/wishlist/toggle/', body: {'card_id': card.id});
    } catch (_) {
      if (mounted) setState(() => cards = [...cards]..[index] = card);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: Text(widget.species.name),
      actions: [
        Padding(
          padding: const EdgeInsets.only(right: 14),
          child: Center(
            child: Text(
              '${widget.species.cardCount} cartas',
              style: const TextStyle(
                color: DexoraColors.cyan,
                fontSize: 12,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
        ),
      ],
    ),
    body: loading
        ? const Center(child: CircularProgressIndicator())
        : error != null
        ? ErrorPane(message: error!, retry: load)
        : cards.isEmpty
        ? const Center(
            child: Text(
              'No hay cartas vinculadas.',
              style: TextStyle(color: DexoraColors.muted),
            ),
          )
        : GridView.builder(
            padding: const EdgeInsets.all(14),
            itemCount: cards.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              childAspectRatio: .64,
              crossAxisSpacing: 11,
              mainAxisSpacing: 11,
            ),
            itemBuilder: (_, index) {
              final card = cards[index];
              return Container(
                decoration: BoxDecoration(
                  color: DexoraColors.navySoft,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: DexoraColors.line),
                ),
                child: Column(
                  children: [
                    Expanded(
                      child: Stack(
                        children: [
                          Positioned.fill(
                            child: ClipRRect(
                              borderRadius: const BorderRadius.vertical(
                                top: Radius.circular(13),
                              ),
                              child: NetworkArtwork(
                                url: card.image,
                                fit: BoxFit.cover,
                              ),
                            ),
                          ),
                          Positioned(
                            right: 6,
                            top: 6,
                            child: _RoundAction(
                              icon: card.isWished
                                  ? Icons.star
                                  : Icons.star_border,
                              color: DexoraColors.gold,
                              onTap: () => toggleWish(card),
                              label: 'Wishlist',
                            ),
                          ),
                          Positioned(
                            left: 6,
                            top: 6,
                            child: _RoundAction(
                              icon: added.contains(card.id)
                                  ? Icons.check
                                  : Icons.add,
                              color: added.contains(card.id)
                                  ? DexoraColors.cyan
                                  : DexoraColors.warmWhite,
                              onTap: () => addCard(card),
                              label: 'Añadir a colección',
                            ),
                          ),
                        ],
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.all(9),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Text(
                            card.name,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontWeight: FontWeight.w800,
                              fontSize: 12,
                            ),
                          ),
                          Text(
                            '${card.setName} · #${card.number}',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: DexoraColors.muted,
                              fontSize: 9,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
  );
}

class _RoundAction extends StatelessWidget {
  const _RoundAction({
    required this.icon,
    required this.color,
    required this.onTap,
    required this.label,
  });
  final IconData icon;
  final Color color;
  final VoidCallback onTap;
  final String label;

  @override
  Widget build(BuildContext context) => IconButton.filledTonal(
    onPressed: onTap,
    tooltip: label,
    icon: Icon(icon, size: 18, color: color),
    style: IconButton.styleFrom(
      backgroundColor: DexoraColors.navy.withValues(alpha: .9),
      minimumSize: const Size(36, 36),
      padding: EdgeInsets.zero,
    ),
  );
}
