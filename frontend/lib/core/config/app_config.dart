import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Build-time configuration passed with `--dart-define`.
///
/// API_BASE_URL is empty by default: the app then calls `/api/v1/...` on the same origin, which is
/// how it runs behind Nginx. Set it only for `flutter run` during development, e.g.
/// `--dart-define=API_BASE_URL=http://localhost:8000`.
class AppConfig {
  const AppConfig({required this.apiBaseUrl, required this.appTitle});

  factory AppConfig.fromEnvironment() => const AppConfig(
        apiBaseUrl: String.fromEnvironment('API_BASE_URL'),
        appTitle: 'Dispute Management System',
      );

  final String apiBaseUrl;
  final String appTitle;

  String get apiRoot => '$apiBaseUrl/api/v1';
}

final appConfigProvider = Provider<AppConfig>((ref) => AppConfig.fromEnvironment());
