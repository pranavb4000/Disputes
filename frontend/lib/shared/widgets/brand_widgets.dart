import 'package:flutter/material.dart';

import '../../core/theme/brand_colors.dart';

/// Standard text-field decoration (kept here rather than in ThemeData for SDK compatibility).
InputDecoration brandInputDecoration({required String label, Widget? prefixIcon, Widget? suffixIcon}) {
  OutlineInputBorder border(Color color, [double width = 1]) => OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: BorderSide(color: color, width: width),
      );
  return InputDecoration(
    labelText: label,
    prefixIcon: prefixIcon,
    suffixIcon: suffixIcon,
    filled: true,
    fillColor: BrandColors.white,
    border: border(BrandColors.border),
    enabledBorder: border(BrandColors.border),
    focusedBorder: border(BrandColors.maroon, 2),
    errorBorder: border(BrandColors.error),
    focusedErrorBorder: border(BrandColors.error, 2),
    labelStyle: const TextStyle(color: BrandColors.textPrimary),
    floatingLabelStyle: const TextStyle(color: BrandColors.maroon),
  );
}

/// White card with a subtle border (guardrail: card backgrounds white or #E8D1C9 tint).
class SectionCard extends StatelessWidget {
  const SectionCard({super.key, required this.child, this.title, this.trailing, this.tinted = false});

  final Widget child;
  final String? title;
  final Widget? trailing;
  final bool tinted;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: tinted ? BrandColors.maroonTint20 : BrandColors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: BrandColors.border),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (title != null) ...[
              Row(
                children: [
                  Expanded(
                    child: Text(
                      title!,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                    ),
                  ),
                  if (trailing != null) trailing!,
                ],
              ),
              const SizedBox(height: 16),
            ],
            child,
          ],
        ),
      ),
    );
  }
}

enum BannerKind { info, warning, error }

/// Notification banner. Yellow tints are reserved for notifications/warnings (max 10% of a screen).
class StatusBanner extends StatelessWidget {
  const StatusBanner({super.key, required this.message, this.kind = BannerKind.info});

  final String message;
  final BannerKind kind;

  @override
  Widget build(BuildContext context) {
    final (Color background, Color accent, IconData icon) = switch (kind) {
      BannerKind.info => (BrandColors.infoBackground, BrandColors.warning, Icons.info_outline),
      BannerKind.warning => (BrandColors.alertBackground, BrandColors.warning, Icons.warning_amber_rounded),
      BannerKind.error => (BrandColors.maroonTint20, BrandColors.maroon, Icons.error_outline),
    };
    return Semantics(
      liveRegion: true,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: background,
          borderRadius: BorderRadius.circular(6),
          border: Border(left: BorderSide(color: accent, width: 4)),
        ),
        child: Row(
          children: [
            Icon(icon, size: 20, color: kind == BannerKind.error ? BrandColors.maroon : BrandColors.textPrimary),
            const SizedBox(width: 10),
            Expanded(child: Text(message, style: const TextStyle(color: BrandColors.textPrimary))),
          ],
        ),
      ),
    );
  }
}
