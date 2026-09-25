import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/brand_colors.dart';
import '../../features/auth/application/auth_controller.dart';
import 'brand_wordmark.dart';

/// A navigation entry in the side rail. Module entries stay disabled until their phase ships.
class ShellDestination {
  const ShellDestination({required this.label, required this.icon, this.enabled = true});

  final String label;
  final IconData icon;
  final bool enabled;
}

/// Standard page frame: maroon top bar (guardrail §3.1), side navigation, content area.
class AppShell extends ConsumerWidget {
  const AppShell({
    super.key,
    required this.title,
    required this.body,
    required this.destinations,
    this.selectedIndex = 0,
    this.onDestinationSelected,
  });

  final String title;
  final Widget body;
  final List<ShellDestination> destinations;
  final int selectedIndex;
  final ValueChanged<int>? onDestinationSelected;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    final wide = MediaQuery.sizeOf(context).width >= 900;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: BrandColors.maroon,
        foregroundColor: BrandColors.white,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        toolbarHeight: 64,
        titleSpacing: 24,
        title: Row(
          children: [
            const BrandWordmark(size: 20),
            const SizedBox(width: 16),
            Container(width: 1, height: 28, color: Colors.white54),
            const SizedBox(width: 16),
            Flexible(
              child: Text(
                title,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: BrandColors.white, fontSize: 16),
              ),
            ),
          ],
        ),
        actions: [
          if (user != null) _UserMenu(displayName: user.displayName, username: user.username),
          const SizedBox(width: 16),
        ],
      ),
      body: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          NavigationRail(
            extended: wide,
            minExtendedWidth: 220,
            backgroundColor: BrandColors.white,
            selectedIndex: selectedIndex,
            onDestinationSelected: onDestinationSelected,
            indicatorColor: BrandColors.maroonTint20,
            selectedIconTheme: const IconThemeData(color: BrandColors.maroon),
            selectedLabelTextStyle: const TextStyle(color: BrandColors.maroon, fontWeight: FontWeight.w700),
            unselectedIconTheme: const IconThemeData(color: BrandColors.textPrimary),
            unselectedLabelTextStyle: const TextStyle(color: BrandColors.textPrimary),
            labelType: wide ? NavigationRailLabelType.none : NavigationRailLabelType.all,
            destinations: [
              for (final d in destinations)
                NavigationRailDestination(
                  icon: Icon(d.icon),
                  label: Text(d.label),
                  disabled: !d.enabled,
                ),
            ],
          ),
          const VerticalDivider(width: 1),
          Expanded(child: body),
        ],
      ),
    );
  }
}

class _UserMenu extends ConsumerWidget {
  const _UserMenu({required this.displayName, required this.username});

  final String displayName;
  final String username;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return PopupMenuButton<String>(
      tooltip: 'Account',
      offset: const Offset(0, 56),
      onSelected: (value) {
        if (value == 'logout') {
          unawaited(ref.read(authControllerProvider.notifier).logout());
        }
      },
      itemBuilder: (context) => [
        PopupMenuItem<String>(
          enabled: false,
          child: Text('Signed in as $username', style: const TextStyle(color: BrandColors.textPrimary)),
        ),
        const PopupMenuDivider(),
        const PopupMenuItem<String>(
          value: 'logout',
          child: Row(
            children: [
              Icon(Icons.logout, color: BrandColors.maroon),
              SizedBox(width: 12),
              Text('Log out'),
            ],
          ),
        ),
      ],
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircleAvatar(
              radius: 16,
              backgroundColor: BrandColors.white,
              child: Text(
                displayName.isNotEmpty ? displayName[0].toUpperCase() : '?',
                style: const TextStyle(color: BrandColors.maroon, fontWeight: FontWeight.w700),
              ),
            ),
            const SizedBox(width: 8),
            Text(displayName, style: const TextStyle(color: BrandColors.white)),
            const Icon(Icons.arrow_drop_down, color: BrandColors.white),
          ],
        ),
      ),
    );
  }
}
