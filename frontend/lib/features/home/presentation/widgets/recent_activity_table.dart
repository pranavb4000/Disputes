import 'package:data_table_2/data_table_2.dart';
import 'package:flutter/material.dart';

import '../../../../core/theme/brand_colors.dart';
import '../../../../core/utils/formatters.dart';
import '../../data/models/home_models.dart';

/// Brand table style: maroon header with white text, alternating white / #DEB9AE rows (guardrail §3.1).
class RecentActivityTable extends StatelessWidget {
  const RecentActivityTable({super.key, required this.items});

  final List<ActivityItem> items;

  static String _label(String action) => switch (action) {
        'LOGIN' => 'Signed in',
        'LOGOUT' => 'Signed out',
        _ => action,
      };

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 24),
        child: Text('No activity yet.', style: TextStyle(color: BrandColors.textPrimary)),
      );
    }
    const headerStyle = TextStyle(color: BrandColors.white, fontWeight: FontWeight.w700);
    return SizedBox(
      height: 56.0 + items.length * 48.0,
      child: DataTable2(
        headingRowColor: const WidgetStatePropertyAll(BrandColors.maroon),
        headingRowHeight: 56,
        columnSpacing: 16,
        horizontalMargin: 16,
        minWidth: 560,
        border: const TableBorder(horizontalInside: BorderSide(color: BrandColors.border)),
        // Not const: keeps compatibility across data_table_2 versions.
        columns: [
          DataColumn2(label: Text('When (IST)', style: headerStyle), size: ColumnSize.L),
          DataColumn2(label: Text('Activity', style: headerStyle)),
          DataColumn2(label: Text('Result', style: headerStyle), size: ColumnSize.S),
          DataColumn2(label: Text('IP address', style: headerStyle)),
        ],
        rows: [
          for (final (index, item) in items.indexed)
            DataRow(
              color: WidgetStatePropertyAll(index.isOdd ? BrandColors.maroonTint40 : BrandColors.white),
              cells: [
                DataCell(Text(Formatters.dateTimeIst(item.occurredAt))),
                DataCell(Text(_label(item.action))),
                DataCell(
                  Text(
                    item.outcome == 'SUCCESS' ? 'Success' : 'Failed',
                    style: TextStyle(
                      color: item.outcome == 'SUCCESS' ? BrandColors.textPrimary : BrandColors.maroon,
                      fontWeight: item.outcome == 'SUCCESS' ? FontWeight.normal : FontWeight.w700,
                    ),
                  ),
                ),
                DataCell(Text(item.ipAddress ?? '—')),
              ],
            ),
        ],
      ),
    );
  }
}
