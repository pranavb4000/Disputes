import 'package:flutter/material.dart';

import '../../../../core/theme/brand_colors.dart';
import '../../../../core/utils/formatters.dart';

/// KPI number with a maroon icon (guardrail: KPI icons use the primary colour).
class KpiTile extends StatelessWidget {
  const KpiTile({super.key, required this.label, required this.value, required this.icon, this.attention = false});

  final String label;
  final int value;
  final IconData icon;

  /// Adds a small yellow attention marker (e.g. SLA breaches). Keep yellow usage minimal.
  final bool attention;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: BrandColors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: BrandColors.border),
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(color: BrandColors.maroonTint20, borderRadius: BorderRadius.circular(8)),
            child: Icon(icon, color: BrandColors.maroon),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(color: BrandColors.textPrimary, fontSize: 13)),
                const SizedBox(height: 4),
                Text(
                  Formatters.count(value),
                  style: const TextStyle(
                    color: BrandColors.textPrimary,
                    fontSize: 24,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
          if (attention && value > 0)
            Container(
              width: 10,
              height: 10,
              decoration: const BoxDecoration(color: BrandColors.yellow, shape: BoxShape.circle),
            ),
        ],
      ),
    );
  }
}
