import 'package:flutter/material.dart';

import '../core/api_client.dart';
import '../core/theme.dart';
import '../models/card_item.dart';
import '../widgets/common.dart';

enum LibraryMode { collection, wishlist }

class LibraryScreen extends StatefulWidget {
  const LibraryScreen({super.key, required this.api, required this.mode});
  final ApiClient api;
  final LibraryMode mode;

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> {
  List<_LibraryEntry> items = const [];
  bool loading = true;
  String? error;

  String get endpoint =>
      widget.mode == LibraryMode.collection ? '/collection/' : '/wishlist/';
  String get title =>
      widget.mode == LibraryMode.collection ? 'Mi colección' : 'Wishlist';

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final data = await widget.api.get(endpoint) as Map<String, dynamic>;
      if (!mounted) return;
      setState(() {
        items = (data['results'] as List).map((raw) {
          final item = raw as Map<String, dynamic>;
          return _LibraryEntry(
            id: item['id'] as int,
            card: CardItem.fromJson(item['card'] as Map<String, dynamic>),
            quantity: item['quantity'] as int? ?? 1,
          );
        }).toList();
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

  Future<void> remove(_LibraryEntry entry) async {
    try {
      if (widget.mode == LibraryMode.collection) {
        await widget.api.delete('/collection/${entry.id}/');
      } else {
        await widget.api.post(
          '/wishlist/toggle/',
          body: {'card_id': entry.card.id},
        );
      }
      if (mounted) {
        setState(
          () => items = items.where((item) => item.id != entry.id).toList(),
        );
      }
    } catch (exception) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(exception.toString())));
      }
    }
  }

  @override
  Widget build(BuildContext context) => SafeArea(
    child: Column(
      children: [
        DexoraHeader(
          title: title,
          subtitle: '${items.length} registros',
          trailing: IconButton(
            onPressed: load,
            icon: const Icon(Icons.refresh),
            tooltip: 'Actualizar',
          ),
        ),
        Expanded(
          child: loading
              ? const Center(child: CircularProgressIndicator())
              : error != null
              ? ErrorPane(message: error!, retry: load)
              : items.isEmpty
              ? _EmptyLibrary(mode: widget.mode)
              : RefreshIndicator(
                  onRefresh: load,
                  child: ListView.separated(
                    padding: const EdgeInsets.fromLTRB(14, 6, 14, 20),
                    itemCount: items.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 9),
                    itemBuilder: (_, index) {
                      final entry = items[index];
                      return Card(
                        child: Padding(
                          padding: const EdgeInsets.all(10),
                          child: Row(
                            children: [
                              SizedBox(
                                width: 66,
                                height: 92,
                                child: ClipRRect(
                                  borderRadius: BorderRadius.circular(7),
                                  child: NetworkArtwork(
                                    url: entry.card.image,
                                    fit: BoxFit.cover,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 13),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      entry.card.name,
                                      maxLines: 2,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w800,
                                      ),
                                    ),
                                    const SizedBox(height: 5),
                                    Text(
                                      '${entry.card.setName} · #${entry.card.number}',
                                      style: const TextStyle(
                                        color: DexoraColors.muted,
                                        fontSize: 11,
                                      ),
                                    ),
                                    if (widget.mode == LibraryMode.collection)
                                      Padding(
                                        padding: const EdgeInsets.only(top: 8),
                                        child: Text(
                                          '×${entry.quantity}',
                                          style: const TextStyle(
                                            color: DexoraColors.gold,
                                            fontWeight: FontWeight.w900,
                                          ),
                                        ),
                                      ),
                                  ],
                                ),
                              ),
                              IconButton(
                                onPressed: () => remove(entry),
                                icon: Icon(
                                  widget.mode == LibraryMode.collection
                                      ? Icons.delete_outline
                                      : Icons.star,
                                  color: widget.mode == LibraryMode.collection
                                      ? DexoraColors.danger
                                      : DexoraColors.gold,
                                ),
                                tooltip: 'Retirar',
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
        ),
      ],
    ),
  );
}

class _LibraryEntry {
  const _LibraryEntry({
    required this.id,
    required this.card,
    required this.quantity,
  });
  final int id;
  final CardItem card;
  final int quantity;
}

class _EmptyLibrary extends StatelessWidget {
  const _EmptyLibrary({required this.mode});
  final LibraryMode mode;
  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(28),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            mode == LibraryMode.collection
                ? Icons.style_outlined
                : Icons.star_border,
            size: 42,
            color: DexoraColors.gold,
          ),
          const SizedBox(height: 14),
          Text(
            mode == LibraryMode.collection
                ? 'Tu colección está lista'
                : 'Tu wishlist está lista',
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 7),
          const Text(
            'Las cartas que registres en Dexora aparecerán aquí.',
            textAlign: TextAlign.center,
            style: TextStyle(color: DexoraColors.muted),
          ),
        ],
      ),
    ),
  );
}
