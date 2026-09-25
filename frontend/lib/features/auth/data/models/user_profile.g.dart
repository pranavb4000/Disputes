// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'user_profile.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

UserProfile _$UserProfileFromJson(Map<String, dynamic> json) => UserProfile(
      id: (json['id'] as num).toInt(),
      username: json['username'] as String,
      displayName: json['display_name'] as String,
      authSource: json['auth_source'] as String,
      modules: (json['modules'] as List<dynamic>)
          .map((e) => ModuleAccess.fromJson(e as Map<String, dynamic>))
          .toList(),
      email: json['email'] as String?,
      lastLoginAt: json['last_login_at'] == null
          ? null
          : DateTime.parse(json['last_login_at'] as String),
    );

Map<String, dynamic> _$UserProfileToJson(UserProfile instance) =>
    <String, dynamic>{
      'id': instance.id,
      'username': instance.username,
      'display_name': instance.displayName,
      'email': instance.email,
      'auth_source': instance.authSource,
      'last_login_at': instance.lastLoginAt?.toIso8601String(),
      'modules': instance.modules,
    };

ModuleAccess _$ModuleAccessFromJson(Map<String, dynamic> json) => ModuleAccess(
      code: json['code'] as String,
      name: json['name'] as String,
      isEnabled: json['is_enabled'] as bool,
      roles: (json['roles'] as List<dynamic>).map((e) => e as String).toList(),
      permissions: (json['permissions'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
    );

Map<String, dynamic> _$ModuleAccessToJson(ModuleAccess instance) =>
    <String, dynamic>{
      'code': instance.code,
      'name': instance.name,
      'is_enabled': instance.isEnabled,
      'roles': instance.roles,
      'permissions': instance.permissions,
    };
