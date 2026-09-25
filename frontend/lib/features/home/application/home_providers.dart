import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../auth/application/auth_controller.dart';
import '../data/home_repository.dart';
import '../data/models/home_models.dart';

class HomeData {
  const HomeData({required this.summary, this.upi});

  final HomeSummary summary;
  final ModuleSummary? upi; // null when the user cannot view UPI disputes
}

/// Loads the home page. Auto-disposed so it refreshes each time the page is opened.
final homeDataProvider = FutureProvider.autoDispose<HomeData>((ref) async {
  final repository = ref.watch(homeRepositoryProvider);
  final canViewUpi = ref.watch(
    authControllerProvider.select((s) => s.user?.can('UPI', 'dispute.view') ?? false),
  );

  final summary = await repository.fetchHome();
  ModuleSummary? upi;
  if (canViewUpi) {
    try {
      upi = await repository.fetchModuleSummary('UPI');
    } on ApiException {
      upi = null; // dashboard tiles are optional; the rest of the page still renders
    }
  }
  return HomeData(summary: summary, upi: upi);
});
