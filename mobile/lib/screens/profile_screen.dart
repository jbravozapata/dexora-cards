import 'package:flutter/material.dart';

import '../core/api_client.dart';
import '../core/theme.dart';
import '../widgets/common.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key, required this.api, required this.onLogout});
  final ApiClient api;
  final Future<void> Function() onLogout;

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  Map<String, dynamic>? profile;
  Map<String, dynamic>? dashboard;
  String? error;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    try {
      final results = await Future.wait([
        widget.api.get('/profile/'),
        widget.api.get('/dashboard/'),
      ]);
      if (mounted) {
        setState(() {
          profile = results[0] as Map<String, dynamic>;
          dashboard = results[1] as Map<String, dynamic>;
          error = null;
        });
      }
    } catch (exception) {
      if (mounted) setState(() => error = exception.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    if (error != null) {
      return SafeArea(
        child: ErrorPane(message: error!, retry: load),
      );
    }
    if (profile == null || dashboard == null) {
      return const SafeArea(child: Center(child: CircularProgressIndicator()));
    }
    final name =
        profile!['name'] as String? ??
        profile!['username'] as String? ??
        'Coleccionista';
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.only(bottom: 30),
        children: [
          DexoraHeader(
            title: name,
            subtitle: profile!['motto'] as String? ?? 'Coleccionista Dexora',
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                gradient: const LinearGradient(
                  colors: [DexoraColors.surface, DexoraColors.navySoft],
                ),
                border: Border.all(color: DexoraColors.line),
              ),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 34,
                    backgroundColor: DexoraColors.cyan.withValues(alpha: .14),
                    child: Text(
                      name.characters.first.toUpperCase(),
                      style: const TextStyle(
                        color: DexoraColors.cyan,
                        fontSize: 28,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          profile!['collector_title']
                                  ?.toString()
                                  .toUpperCase() ??
                              'COLECCIONISTA',
                          style: const TextStyle(
                            color: DexoraColors.cyan,
                            letterSpacing: 1.3,
                            fontSize: 10,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(height: 7),
                        Text(
                          profile!['bio'] as String? ??
                              'Tu archivo personal de Pokémon y cartas TCG.',
                          style: const TextStyle(
                            color: DexoraColors.muted,
                            height: 1.4,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              childAspectRatio: 1.75,
              crossAxisSpacing: 10,
              mainAxisSpacing: 10,
              children: [
                _Stat(
                  value: '${dashboard!['species_owned']}',
                  label: 'Pokémon obtenidos',
                ),
                _Stat(
                  value: '${dashboard!['species_progress']}%',
                  label: 'Pokédex completa',
                ),
                _Stat(
                  value: '${dashboard!['cards_different']}',
                  label: 'Cartas diferentes',
                ),
                _Stat(
                  value: '${dashboard!['wishlist_total']}',
                  label: 'En wishlist',
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: OutlinedButton.icon(
              onPressed: widget.onLogout,
              icon: const Icon(Icons.logout),
              label: const Text('Cerrar sesión'),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size.fromHeight(50),
                foregroundColor: DexoraColors.danger,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.value, required this.label});
  final String value;
  final String label;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: DexoraColors.navySoft,
      borderRadius: BorderRadius.circular(14),
      border: Border.all(color: DexoraColors.line),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          value,
          style: const TextStyle(
            color: DexoraColors.cyan,
            fontSize: 22,
            fontWeight: FontWeight.w900,
          ),
        ),
        Text(
          label,
          style: const TextStyle(color: DexoraColors.muted, fontSize: 10),
        ),
      ],
    ),
  );
}
