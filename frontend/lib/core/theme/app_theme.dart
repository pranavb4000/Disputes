import 'package:flutter/material.dart';

import 'brand_colors.dart';

/// Application theme built from the IDFC FIRST Bank guardrails.
///
/// Only component themes whose types are stable across Flutter releases are set here.
/// App bar, card and input styling live in shared widgets (see lib/shared/widgets) instead.
abstract final class AppTheme {
  static const String fontFamily = 'BrandSans';
  static const List<String> fontFallback = ['SymbolFallback'];

  static ThemeData light() {
    const scheme = ColorScheme(
      brightness: Brightness.light,
      primary: BrandColors.maroon,
      onPrimary: BrandColors.white,
      primaryContainer: BrandColors.maroonTint20,
      onPrimaryContainer: BrandColors.maroon,
      secondary: BrandColors.maroonTint80,
      onSecondary: BrandColors.white,
      tertiary: BrandColors.yellow,
      onTertiary: BrandColors.textPrimary,
      error: BrandColors.error,
      onError: BrandColors.white,
      surface: BrandColors.white,
      onSurface: BrandColors.textPrimary,
      outline: BrandColors.border,
      outlineVariant: BrandColors.border,
    );

    final shape = RoundedRectangleBorder(borderRadius: BorderRadius.circular(6));

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      fontFamily: fontFamily,
      fontFamilyFallback: fontFallback,
      scaffoldBackgroundColor: const Color(0xFFF7F7F8),
      dividerColor: BrandColors.border,
      disabledColor: BrandColors.disabled,
      hoverColor: BrandColors.maroonTint20.withValues(alpha: 0.5),
      textTheme: ThemeData.light().textTheme.apply(
            bodyColor: BrandColors.textPrimary,
            displayColor: BrandColors.textPrimary,
            fontFamily: fontFamily,
            fontFamilyFallback: fontFallback,
          ),
      // Primary action: maroon fill, white text.
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: BrandColors.maroon,
          foregroundColor: BrandColors.white,
          disabledBackgroundColor: BrandColors.disabled,
          minimumSize: const Size(120, 44),
          shape: shape,
          textStyle: const TextStyle(fontWeight: FontWeight.w700, fontFamily: fontFamily),
        ),
      ),
      // Secondary action: white with a maroon border (guardrail §3.1).
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: BrandColors.maroon,
          backgroundColor: BrandColors.white,
          side: const BorderSide(color: BrandColors.maroon),
          minimumSize: const Size(120, 44),
          shape: shape,
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(foregroundColor: BrandColors.maroon),
      ),
      dividerTheme: const DividerThemeData(color: BrandColors.border, thickness: 1, space: 1),
      progressIndicatorTheme: const ProgressIndicatorThemeData(color: BrandColors.maroon),
    );
  }
}
