import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/brand_colors.dart';
import '../../../shared/widgets/brand_wordmark.dart';
import '../application/auth_controller.dart';

/// Shown while the app checks for an existing session (refresh cookie) after a page load.
class SplashPage extends ConsumerStatefulWidget {
  const SplashPage({super.key});

  @override
  ConsumerState<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends ConsumerState<SplashPage> {
  @override
  void initState() {
    super.initState();
    // Run after the first frame so the router is ready to react to the new auth state.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      unawaited(ref.read(authControllerProvider.notifier).restoreSession());
    });
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: BrandColors.maroon,
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            BrandWordmark(size: 32),
            SizedBox(height: 24),
            SizedBox(
              width: 28,
              height: 28,
              child: CircularProgressIndicator(color: BrandColors.white, strokeWidth: 3),
            ),
          ],
        ),
      ),
    );
  }
}
