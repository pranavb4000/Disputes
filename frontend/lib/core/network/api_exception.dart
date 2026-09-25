import 'package:dio/dio.dart';

/// A failed API call, carrying the server's safe message and error code
/// from the standard envelope `{success, data, message, error_code}`.
class ApiException implements Exception {
  const ApiException(this.message, {this.errorCode, this.statusCode});

  factory ApiException.fromDio(DioException error) {
    final response = error.response;
    final body = response?.data;
    if (body is Map<String, dynamic>) {
      final message = body['message'];
      final code = body['error_code'];
      return ApiException(
        message is String && message.isNotEmpty ? message : _fallbackMessage(error),
        errorCode: code is String ? code : null,
        statusCode: response?.statusCode,
      );
    }
    return ApiException(_fallbackMessage(error), statusCode: response?.statusCode);
  }

  final String message;
  final String? errorCode;
  final int? statusCode;

  bool get isUnauthorized => statusCode == 401;

  static String _fallbackMessage(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.sendTimeout:
        return 'The server took too long to respond. Please try again.';
      case DioExceptionType.connectionError:
        return 'Cannot reach the server. Check your network connection.';
      default:
        return 'Something went wrong. Please try again.';
    }
  }

  @override
  String toString() => 'ApiException($statusCode, $errorCode): $message';
}

/// Returns `data` from a successful envelope, or throws [ApiException].
T unwrapEnvelope<T>(Response<dynamic> response, T Function(Object? data) parse) {
  final body = response.data;
  if (body is Map<String, dynamic> && body['success'] == true) {
    return parse(body['data']);
  }
  final message = body is Map<String, dynamic> ? body['message'] : null;
  throw ApiException(
    message is String ? message : 'Unexpected response from server',
    errorCode: body is Map<String, dynamic> ? body['error_code'] as String? : null,
    statusCode: response.statusCode,
  );
}
