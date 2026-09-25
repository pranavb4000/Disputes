import 'package:dio/dio.dart';

import 'token_store.dart';

/// Attaches the Bearer token and, on a 401, refreshes the session once and retries the request.
///
/// QueuedInterceptor serialises error handling, so many parallel 401s trigger a single refresh.
/// Retries go through [retryDio] (which has no auth interceptor) to avoid re-entering this queue.
class AuthInterceptor extends QueuedInterceptor {
  AuthInterceptor({
    required this.tokenStore,
    required this.refresh,
    required this.onSessionExpired,
    required this.retryDio,
  });

  final TokenStore tokenStore;
  final Future<bool> Function() refresh;
  final void Function() onSessionExpired;
  final Dio retryDio;

  static const String _retriedKey = 'dms_retried';

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = tokenStore.accessToken;
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    final options = err.requestOptions;
    if (err.response?.statusCode != 401 || options.extra[_retriedKey] == true) {
      handler.next(err);
      return;
    }

    // A request queued behind another 401 may find the token already refreshed.
    final sentHeader = options.headers['Authorization'];
    final current = tokenStore.accessToken;
    var refreshed = current != null && sentHeader != 'Bearer $current';
    if (!refreshed) {
      refreshed = await refresh();
    }
    if (!refreshed || tokenStore.accessToken == null) {
      onSessionExpired();
      handler.next(err);
      return;
    }

    options.extra[_retriedKey] = true;
    options.headers['Authorization'] = 'Bearer ${tokenStore.accessToken}';
    try {
      handler.resolve(await retryDio.fetch<dynamic>(options));
    } on DioException catch (retryError) {
      handler.next(retryError);
    }
  }
}
