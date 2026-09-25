import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/token_store.dart';
import '../../../core/network/api_exception.dart';
import '../data/auth_repository.dart';
import '../data/models/auth_session.dart';
import '../data/models/user_profile.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

@immutable
class AuthState {
  const AuthState({
    required this.status,
    this.user,
    this.isBusy = false,
    this.errorMessage,
    this.sessionExpired = false,
  });

  const AuthState.unknown() : this(status: AuthStatus.unknown);

  final AuthStatus status;
  final UserProfile? user;
  final bool isBusy;
  final String? errorMessage;
  final bool sessionExpired;

  bool get isAuthenticated => status == AuthStatus.authenticated;
}

/// Owns the login state. The router listens to it to decide which page to show.
class AuthController extends Notifier<AuthState> {
  @override
  AuthState build() => const AuthState.unknown();

  AuthRepository get _repository => ref.read(authRepositoryProvider);
  TokenStore get _tokens => ref.read(tokenStoreProvider);

  void _apply(AuthSession session) {
    _tokens.save(session.accessToken, session.expiresAt);
    state = AuthState(status: AuthStatus.authenticated, user: session.user);
  }

  /// Called once at start-up: silently restores the session from the refresh cookie.
  Future<void> restoreSession() async {
    try {
      final session = await _repository.refresh();
      if (session != null) {
        _apply(session);
        return;
      }
    } on ApiException {
      // Server unreachable: fall through to the login page, which will show errors on submit.
    }
    _tokens.clear();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }

  Future<bool> login(String username, String password) async {
    state = AuthState(status: AuthStatus.unauthenticated, isBusy: true, sessionExpired: state.sessionExpired);
    try {
      _apply(await _repository.login(username, password));
      return true;
    } on ApiException catch (e) {
      state = AuthState(status: AuthStatus.unauthenticated, errorMessage: e.message);
      return false;
    }
  }

  /// Used by the HTTP interceptor when an access token expires. Returns true if refreshed.
  Future<bool> refreshSilently() async {
    try {
      final session = await _repository.refresh();
      if (session == null) return false;
      _apply(session);
      return true;
    } on ApiException {
      return false;
    }
  }

  Future<void> logout() async {
    final token = _tokens.accessToken;
    _tokens.clear();
    state = const AuthState(status: AuthStatus.unauthenticated);
    await _repository.logout(token);
  }

  void sessionExpired() {
    _tokens.clear();
    state = const AuthState(status: AuthStatus.unauthenticated, sessionExpired: true);
  }
}

final authControllerProvider = NotifierProvider<AuthController, AuthState>(AuthController.new);
