import 'package:flutter/material.dart';

import 'auth/auth_controller.dart';
import 'core/api_client.dart';
import 'core/theme.dart';
import 'screens/login_screen.dart';
import 'screens/shell_screen.dart';

class DexoraApp extends StatefulWidget {
  const DexoraApp({super.key});

  @override
  State<DexoraApp> createState() => _DexoraAppState();
}

class _DexoraAppState extends State<DexoraApp> {
  late final ApiClient api = ApiClient();
  late final AuthController auth = AuthController(api)..initialize();

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'Dexora Cards',
    debugShowCheckedModeBanner: false,
    theme: buildDexoraTheme(),
    home: AnimatedBuilder(
      animation: auth,
      builder: (context, _) {
        if (!auth.initialized) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        if (!auth.authenticated) return LoginScreen(controller: auth);
        return ShellScreen(api: api, onLogout: auth.logout);
      },
    ),
  );
}
