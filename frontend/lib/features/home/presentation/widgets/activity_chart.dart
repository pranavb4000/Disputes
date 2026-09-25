import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../../../../core/theme/brand_colors.dart';
import '../../data/models/home_models.dart';

/// Donut chart of the user's recent activity (maroon family colours; guardrail: chart accents).
class ActivityChart extends StatelessWidget {
  const ActivityChart({super.key, required this.items});

  final List<ActivityItem> items;

  @override
  Widget build(BuildContext context) {
    final signIns = items.where((i) => i.action == 'LOGIN' && i.outcome == 'SUCCESS').length;
    final signOuts = items.where((i) => i.action == 'LOGOUT').length;
    final other = items.length - signIns - signOuts;
    final slices = <(String, int, Color)>[
      ('Sign-ins', signIns, BrandColors.maroon),
      ('Sign-outs', signOuts, BrandColors.maroonTint80),
      ('Other', other, BrandColors.disabled),
    ].where((s) => s.$2 > 0).toList();

    if (slices.isEmpty) {
      return const SizedBox(height: 180, child: Center(child: Text('No activity yet.')));
    }

    return Row(
      children: [
        SizedBox(
          width: 180,
          height: 180,
          child: PieChart(
            PieChartData(
              centerSpaceRadius: 44,
              sectionsSpace: 2,
              sections: [
                for (final (_, value, color) in slices)
                  PieChartSectionData(
                    value: value.toDouble(),
                    color: color,
                    radius: 36,
                    title: '$value',
                    titleStyle: const TextStyle(color: BrandColors.white, fontWeight: FontWeight.w700),
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(width: 24),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            for (final (label, value, color) in slices)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(width: 12, height: 12, color: color),
                    const SizedBox(width: 8),
                    Text('$label ($value)', style: const TextStyle(color: BrandColors.textPrimary)),
                  ],
                ),
              ),
          ],
        ),
      ],
    );
  }
}
