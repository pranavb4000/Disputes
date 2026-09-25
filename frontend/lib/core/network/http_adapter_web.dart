import 'package:dio/browser.dart';
import 'package:dio/dio.dart';

/// On web, send cookies with requests so the HttpOnly refresh cookie reaches /api/v1/auth/*.
/// (Needed only when API_BASE_URL points to another origin during development; harmless otherwise.)
void configureHttpAdapter(Dio dio) {
  final adapter = BrowserHttpClientAdapter();
  adapter.withCredentials = true;
  dio.httpClientAdapter = adapter;
}
