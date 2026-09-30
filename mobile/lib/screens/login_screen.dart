import 'package:flutter/material.dart';

import '../auth/auth_controller.dart';
import '../core/theme.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.controller});
  final AuthController controller;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final username = TextEditingController();
  final password = TextEditingController();

  @override
  void dispose() {
    username.dispose();
    password.dispose();
    super.dispose();
  }

  Future<void> submit() async {
    if (username.text.trim().isEmpty || password.text.isEmpty) return;
    FocusScope.of(context).unfocus();
    await widget.controller.login(username.text, password.text);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(28),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 430),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const _BrandMark(),
                const SizedBox(height: 42),
                const Text(
                  'Tu colección, siempre contigo.',
                  style: TextStyle(
                    fontSize: 32,
                    height: 1.05,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 10),
                const Text(
                  'Accede al Cardex, registra tus cartas y completa tus 1025 Pokémon.',
                  style: TextStyle(color: DexoraColors.muted, height: 1.5),
                ),
                const SizedBox(height: 30),
                TextField(
                  controller: username,
                  textInputAction: TextInputAction.next,
                  autofillHints: const [AutofillHints.username],
                  decoration: const InputDecoration(
                    labelText: 'Usuario',
                    prefixIcon: Icon(Icons.person_outline),
                  ),
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: password,
                  obscureText: true,
                  onSubmitted: (_) => submit(),
                  autofillHints: const [AutofillHints.password],
                  decoration: const InputDecoration(
                    labelText: 'Contraseña',
                    prefixIcon: Icon(Icons.lock_outline),
                  ),
                ),
                if (widget.controller.error != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 14),
                    child: Text(
                      widget.controller.error!,
                      style: const TextStyle(color: DexoraColors.danger),
                    ),
                  ),
                const SizedBox(height: 20),
                FilledButton(
                  onPressed: widget.controller.busy ? null : submit,
                  style: FilledButton.styleFrom(
                    minimumSize: const Size.fromHeight(52),
                    foregroundColor: DexoraColors.navy,
                    textStyle: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                  child: widget.controller.busy
                      ? const SizedBox.square(
                          dimension: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Ingresar'),
                ),
                const SizedBox(height: 22),
                const Text(
                  'Acceso protegido mediante la API privada de Dexora.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: DexoraColors.muted, fontSize: 11),
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}

class _BrandMark extends StatelessWidget {
  const _BrandMark();
  @override
  Widget build(BuildContext context) => Row(
    children: [
      Image.asset(
        'assets/images/dexora-mark.png',
        width: 58,
        height: 70,
        fit: BoxFit.contain,
      ),
      const SizedBox(width: 14),
      const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'DEXORA',
            style: TextStyle(
              fontSize: 21,
              letterSpacing: 1.2,
              fontWeight: FontWeight.w900,
            ),
          ),
          Text(
            'C A R D S',
            style: TextStyle(
              color: DexoraColors.cyan,
              fontSize: 10,
              letterSpacing: 3,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    ],
  );
}
