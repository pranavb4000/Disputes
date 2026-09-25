import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/config/app_config.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/network/dio_factory.dart';
import 'models/auth_session.dart';

/// Calls the auth endpoints. Uses a plain Dio (no auth interceptor) so a failing refresh can
/// never trigger another refresh.
class AuthRepository {
  AuthRepository(this._dio);

  final Dio _dio;

  Future<AuthSession> login(String username, String password) async {
    try {
      final response = await _dio.post<dynamic>(
        '/auth/login',
        data: {'username': username, 'password': password},
      );
      return unwrapEnvelope(response, (data) => AuthSession.fromJson(data! as Map<String, dynamic>));
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// Returns a new session, or null when there is no valid refresh cookie (user must log in).
  Future<AuthSession?> refresh() async {
    try {
      final response = await _dio.post<dynamic>('/auth/refresh');
      return unwrapEnvelope(response, (data) => AuthSession.fromJson(data! as Map<String, dynamic>));
    } on DioException catch (e) {
      final error = ApiException.fromDio(e);
      if (error.statusCode == 401 || error.statusCode == 403) {
        return null;
      }
      throw error;
    }
  }

  /// Best effort: the local session is cleared even if the server cannot be reached.
  Future<void> logout(String? accessToken) async {
    try {
      await _dio.post<dynamic>(
        '/auth/logout',
        options: Options(
          headers: {if (accessToken != null) 'Authorization': 'Bearer $accessToken'},
        ),
      );
    } on DioException {
      // Deliberately swallowed: the refresh cookie expires on its own and the access token is short-lived.
    }
  }
}

final authDioProvider = Provider<Dio>((ref) => buildDio(ref.watch(appConfigProvider)));

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(ref.watch(authDioProvider)),
);
