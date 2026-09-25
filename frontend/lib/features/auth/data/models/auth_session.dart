import 'user_profile.dart';

/// Result of /auth/login and /auth/refresh (backend `TokenResponse`).
class AuthSession {
  const AuthSession({required this.accessToken, required this.expiresAt, required this.user});

  factory AuthSession.fromJson(Map<String, dynamic> json) => AuthSession(
        accessToken: json['access_token'] as String,
        expiresAt: DateTime.parse(json['expires_at'] as String),
        user: UserProfile.fromJson(json['user'] as Map<String, dynamic>),
      );

  final String accessToken;
  final DateTime expiresAt;
  final UserProfile user;
}
