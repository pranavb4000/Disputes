import 'package:json_annotation/json_annotation.dart';

part 'user_profile.g.dart';

/// Mirrors the backend `UserProfile` schema (GET /api/v1/auth/me).
///
/// Regenerate `user_profile.g.dart` after changing fields:
///   dart run build_runner build --delete-conflicting-outputs
@JsonSerializable(fieldRename: FieldRename.snake)
class UserProfile {
  const UserProfile({
    required this.id,
    required this.username,
    required this.displayName,
    required this.authSource,
    required this.modules,
    this.email,
    this.lastLoginAt,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) => _$UserProfileFromJson(json);

  final int id;
  final String username;
  final String displayName;
  final String? email;
  final String authSource;
  final DateTime? lastLoginAt;
  final List<ModuleAccess> modules;

  Map<String, dynamic> toJson() => _$UserProfileToJson(this);

  bool can(String moduleCode, String permission) => modules.any(
        (m) => m.code == moduleCode && m.isEnabled && m.permissions.contains(permission),
      );
}

@JsonSerializable(fieldRename: FieldRename.snake)
class ModuleAccess {
  const ModuleAccess({
    required this.code,
    required this.name,
    required this.isEnabled,
    required this.roles,
    required this.permissions,
  });

  factory ModuleAccess.fromJson(Map<String, dynamic> json) => _$ModuleAccessFromJson(json);

  final String code;
  final String name;
  final bool isEnabled;
  final List<String> roles;
  final List<String> permissions;

  Map<String, dynamic> toJson() => _$ModuleAccessToJson(this);
}
