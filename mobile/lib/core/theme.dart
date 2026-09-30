import 'package:flutter/material.dart';

abstract final class DexoraColors {
  static const navy = Color(0xFF061329);
  static const navySoft = Color(0xFF0B1E3A);
  static const surface = Color(0xFF0D2342);
  static const cyan = Color(0xFF18C5E4);
  static const gold = Color(0xFFF2C14E);
  static const warmWhite = Color(0xFFF7F9FC);
  static const muted = Color(0xFF9AAFC6);
  static const line = Color(0xFF203B5B);
  static const danger = Color(0xFFEF6675);
}

ThemeData buildDexoraTheme() {
  final scheme =
      ColorScheme.fromSeed(
        seedColor: DexoraColors.cyan,
        brightness: Brightness.dark,
        surface: DexoraColors.navySoft,
      ).copyWith(
        primary: DexoraColors.cyan,
        secondary: DexoraColors.gold,
        error: DexoraColors.danger,
      );
  return ThemeData(
    brightness: Brightness.dark,
    colorScheme: scheme,
    scaffoldBackgroundColor: DexoraColors.navy,
    useMaterial3: true,
    appBarTheme: const AppBarTheme(
      elevation: 0,
      backgroundColor: DexoraColors.navy,
      foregroundColor: DexoraColors.warmWhite,
    ),
    navigationBarTheme: NavigationBarThemeData(
      height: 72,
      backgroundColor: const Color(0xFF041022),
      indicatorColor: DexoraColors.cyan.withValues(alpha: .16),
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => TextStyle(
          color: states.contains(WidgetState.selected)
              ? DexoraColors.cyan
              : DexoraColors.muted,
          fontSize: 10,
          fontWeight: FontWeight.w700,
        ),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: DexoraColors.navySoft,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: DexoraColors.line),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: DexoraColors.line),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: DexoraColors.cyan, width: 1.5),
      ),
    ),
    cardTheme: CardThemeData(
      color: DexoraColors.navySoft,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: const BorderSide(color: DexoraColors.line),
      ),
    ),
  );
}
