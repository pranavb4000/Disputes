import 'dart:math';

import 'package:dio/dio.dart';

import '../config/app_config.dart';
import 'http_adapter.dart';

/// Header the backend requires on cookie-authenticated endpoints (CSRF defence).
const String clientHeaderName = 'X-DMS-Client';
const String clientHeaderValue = 'web';

/// Creates a Dio instance with the shared defaults. Auth handling is added separately.
Dio buildDio(AppConfig config) {
  final dio = Dio(
    BaseOptions(
      baseUrl: config.apiRoot,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 60),
      contentType: Headers.jsonContentType,
      responseType: ResponseType.json,
      headers: {clientHeaderName: clientHeaderValue, 'Accept': 'application/json'},
      // Let non-2xx responses through as DioException so ApiException can read the envelope.
      validateStatus: (status) => status != null && status >= 200 && status < 300,
    ),
  );
  configureHttpAdapter(dio);
  dio.interceptors.add(RequestIdInterceptor());
  return dio;
}

/// Adds an X-Request-ID so a UI action can be traced through Nginx, the API and the logs.
class RequestIdInterceptor extends Interceptor {
  final Random _random = Random.secure();

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.headers['X-Request-ID'] ??= List.generate(16, (_) => _random.nextInt(256))
        .map((b) => b.toRadixString(16).padLeft(2, '0'))
        .join();
    handler.next(options);
  }
}
