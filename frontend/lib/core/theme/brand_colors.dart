import 'package:flutter/material.dart';

/// IDFC FIRST Bank UI guardrails (IDFC_UI_GUARDRAILS.md §2).
///
/// Rules to remember:
/// * Maroon is the primary colour: top bar, primary buttons, active navigation, table headers,
///   KPI icons and chart accents.
/// * Yellow is for warnings, notifications and attention indicators ONLY, and must not exceed
///   10% of any screen.
abstract final class BrandColors {
  // 2.1 Primary (Maroon) — Pantone 7427C
  static const Color maroon = Color(0xFF9D1D27);

  // 2.2 Highlight (Yellow) — max 10% of any surface
  static const Color yellow = Color(0xFFFFCB05);

  // 2.3 Primary tints
  static const Color maroonTint80 = Color(0xFFBD7061); // card backgrounds, hover states
  static const Color maroonTint60 = Color(0xFFD9ADA1); // table alternating rows (per §2.3)
  static const Color maroonTint40 = Color(0xFFDEB9AE); // secondary backgrounds; table rows per §3.1
  static const Color maroonTint20 = Color(0xFFE8D1C9); // subtle highlights, card tint

  // 2.4 Highlight tints
  static const Color warning = Color(0xFFFFCD00); // pending status, warnings
  static const Color alertBackground = Color(0xFFFFE592); // alert backgrounds
  static const Color infoBackground = Color(0xFFFFF1C8); // info notifications
  static const Color lightAlert = Color(0xFFFFF6DE); // light alerts

  // 2.5 Neutral greys
  static const Color textPrimary = Color(0xFF54565B);
  static const Color textSecondary = Color(0xFFBCBEC0);
  static const Color disabled = Color(0xFFC7C8CA);
  static const Color border = Color(0xFFDCDDDE);

  static const Color white = Color(0xFFFFFFFF);

  // Not defined in the guardrails excerpt received so far — confirm with the brand team.
  static const Color error = Color(0xFFB3261E);
}
