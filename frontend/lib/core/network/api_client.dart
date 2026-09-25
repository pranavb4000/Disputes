import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/auth/application/auth_controller.dart';
import '../auth/auth_interceptor.dart';
import '../auth/token_store.dart';
import '../config/app_config.dart';
import 'dio_factory.dart';

/// Dio for all authenticated API calls (everything except the auth endpoints themselves).
final apiDioProvider = Provider<Dio>((ref) {
  final config = ref.watch(appConfigProvider);
  final dio = buildDio(config);
  dio.interceptors.add(
    AuthInterceptor(
      tokenStore: ref.watch(tokenStoreProvider),
      refresh: () => ref.read(authControllerProvider.notifier).refreshSilently(),
      onSessionExpired: () => ref.read(authControllerProvider.notifier).sessionExpired(),
      retryDio: buildDio(config),
    ),
  );
  return dio;
});
