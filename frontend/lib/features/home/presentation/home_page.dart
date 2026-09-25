import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/brand_colors.dart';
import '../../../core/utils/formatters.dart';
import '../../../shared/widgets/app_shell.dart';
import '../../../shared/widgets/brand_widgets.dart';
import '../application/home_providers.dart';
import 'widgets/activity_chart.dart';
import 'widgets/kpi_tile.dart';
import 'widgets/module_card.dart';
import 'widgets/recent_activity_table.dart';

const _destinations = [
  ShellDestination(label: 'Home', icon: Icons.home_outlined),
  ShellDestination(label: 'UPI', icon: Icons.account_balance_outlined, enabled: false),
  ShellDestination(label: 'IMPS', icon: Icons.swap_horiz, enabled: false),
  ShellDestination(label: 'AEPS', icon: Icons.fingerprint, enabled: false),
  ShellDestination(label: 'E-Toll', icon: Icons.toll, enabled: false),
];

class HomePage extends ConsumerWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final home = ref.watch(homeDataProvider);

    return AppShell(
      title: 'Dispute Management System',
      destinations: _destinations,
      body: home.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                StatusBanner(
                  message: error is ApiException ? error.message : 'Could not load the home page.',
                  kind: BannerKind.error,
                ),
                const SizedBox(height: 16),
                OutlinedButton(
                  onPressed: () => ref.invalidate(homeDataProvider),
                  child: const Text('Try again'),
                ),
              ],
            ),
          ),
        ),
        data: (data) => _HomeContent(data: data),
      ),
    );
  }
}

class _HomeContent extends StatelessWidget {
  const _HomeContent({required this.data});

  final HomeData data;

  @override
  Widget build(BuildContext context) {
    final summary = data.summary;
    final textTheme = Theme.of(context).textTheme;
    final upi = data.upi;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Welcome, ${summary.greetingName}',
            style: textTheme.headlineSmall?.copyWith(color: BrandColors.maroon, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 4),
          Text(
            summary.lastLoginAt == null
                ? 'This is your first sign-in.'
                : 'Previous sign-in: ${Formatters.dateTimeIst(summary.lastLoginAt)}',
            style: const TextStyle(color: BrandColors.textPrimary),
          ),
          if (summary.notice != null) ...[
            const SizedBox(height: 16),
            StatusBanner(message: summary.notice!),
          ],
          if (upi != null) ...[
            const SizedBox(height: 24),
            Text('UPI at a glance', style: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 12),
            LayoutBuilder(
              builder: (context, constraints) {
                final tiles = [
                  KpiTile(label: 'Open disputes', value: upi.openDisputes, icon: Icons.inbox_outlined),
                  KpiTile(label: 'Pending approval', value: upi.pendingApproval, icon: Icons.fact_check_outlined),
                  KpiTile(
                    label: 'SLA breached',
                    value: upi.breachedSla,
                    icon: Icons.timer_off_outlined,
                    attention: true,
                  ),
                ];
                final columns = constraints.maxWidth >= 900 ? 3 : 1;
                const gap = 16.0;
                final width = (constraints.maxWidth - gap * (columns - 1)) / columns;
                return Wrap(
                  spacing: gap,
                  runSpacing: gap,
                  children: [for (final t in tiles) SizedBox(width: width, child: t)],
                );
              },
            ),
          ],
          const SizedBox(height: 24),
          Text('Modules', style: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 12),
          Wrap(
            spacing: 16,
            runSpacing: 16,
            children: [
              for (final module in summary.modules)
                ModuleCard(
                  module: module,
                  onOpen: () => ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('${module.name} workspace arrives in Phase 1a.')),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 24),
          LayoutBuilder(
            builder: (context, constraints) {
              final table = SectionCard(
                title: 'Your recent activity',
                child: RecentActivityTable(items: summary.recentActivity),
              );
              final chart = SectionCard(
                title: 'Activity mix',
                child: ActivityChart(items: summary.recentActivity),
              );
              if (constraints.maxWidth < 1100) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [table, const SizedBox(height: 16), chart],
                );
              }
              return Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(flex: 3, child: table),
                  const SizedBox(width: 16),
                  Expanded(flex: 2, child: chart),
                ],
              );
            },
          ),
        ],
      ),
    );
  }
}
