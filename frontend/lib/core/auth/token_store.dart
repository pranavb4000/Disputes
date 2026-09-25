import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Holds the short-lived access token IN MEMORY ONLY (ARCHITECTURE.md §9.2).
///
/// It is never written to localStorage/sessionStorage. After a page reload the app restores the
/// session through /auth/refresh, which uses the HttpOnly refresh cookie the browser keeps.
class TokenStore {
  String? _accessToken;
  DateTime? _expiresAt;

  String? get accessToken => _accessToken;
  DateTime? get expiresAt => _expiresAt;
  bool get hasToken => _accessToken != null;

  void save(String token, DateTime expiresAt) {
    _accessToken = token;
    _expiresAt = expiresAt;
  }

  void clear() {
    _accessToken = null;
    _expiresAt = null;
  }
}

final tokenStoreProvider = Provider<TokenStore>((ref) => TokenStore());
