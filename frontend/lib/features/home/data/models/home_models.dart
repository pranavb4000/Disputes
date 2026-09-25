/// Models for GET /api/v1/home and GET /api/v1/{module}/summary.
/// (Hand-written fromJson; see auth/data/models for the json_serializable pattern.)
class HomeSummary {
  const HomeSummary({
    required this.greetingName,
    required this.modules,
    required this.recentActivity,
    this.lastLoginAt,
    this.notice,
  });

  factory HomeSummary.fromJson(Map<String, dynamic> json) => HomeSummary(
        greetingName: json['greeting_name'] as String,
        lastLoginAt: _date(json['last_login_at']),
        modules: [
          for (final m in json['modules'] as List<dynamic>) ModuleCardData.fromJson(m as Map<String, dynamic>),
        ],
        recentActivity: [
          for (final a in json['recent_activity'] as List<dynamic>) ActivityItem.fromJson(a as Map<String, dynamic>),
        ],
        notice: json['notice'] as String?,
      );

  final String greetingName;
  final DateTime? lastLoginAt;
  final List<ModuleCardData> modules;
  final List<ActivityItem> recentActivity;
  final String? notice;
}

class ModuleCardData {
  const ModuleCardData({
    required this.code,
    required this.name,
    required this.isEnabled,
    required this.hasAccess,
    required this.roles,
    this.description,
  });

  factory ModuleCardData.fromJson(Map<String, dynamic> json) => ModuleCardData(
        code: json['code'] as String,
        name: json['name'] as String,
        description: json['description'] as String?,
        isEnabled: json['is_enabled'] as bool,
        hasAccess: json['has_access'] as bool,
        roles: [for (final r in json['roles'] as List<dynamic>) r as String],
      );

  final String code;
  final String name;
  final String? description;
  final bool isEnabled;
  final bool hasAccess;
  final List<String> roles;
}

class ActivityItem {
  const ActivityItem({required this.occurredAt, required this.action, required this.outcome, this.ipAddress});

  factory ActivityItem.fromJson(Map<String, dynamic> json) => ActivityItem(
        occurredAt: DateTime.parse(json['occurred_at'] as String),
        action: json['action'] as String,
        outcome: json['outcome'] as String,
        ipAddress: json['ip_address'] as String?,
      );

  final DateTime occurredAt;
  final String action;
  final String outcome;
  final String? ipAddress;
}

class ModuleSummary {
  const ModuleSummary({
    required this.moduleCode,
    required this.openDisputes,
    required this.pendingApproval,
    required this.breachedSla,
    required this.isPlaceholder,
  });

  factory ModuleSummary.fromJson(Map<String, dynamic> json) => ModuleSummary(
        moduleCode: json['module_code'] as String,
        openDisputes: (json['open_disputes'] as num).toInt(),
        pendingApproval: (json['pending_approval'] as num).toInt(),
        breachedSla: (json['breached_sla'] as num).toInt(),
        isPlaceholder: json['is_placeholder'] as bool? ?? false,
      );

  final String moduleCode;
  final int openDisputes;
  final int pendingApproval;
  final int breachedSla;
  final bool isPlaceholder;
}

DateTime? _date(Object? value) => value is String ? DateTime.parse(value) : null;
