import 'package:dms_web/features/auth/data/auth_repository.dart';
import 'package:dms_web/features/auth/data/models/auth_session.dart';
import 'package:dms_web/features/auth/data/models/user_profile.dart';
import 'package:mocktail/mocktail.dart';

class MockAuthRepository extends Mock implements AuthRepository {}

AuthSession sampleSession() => AuthSession(
      accessToken: 'access-token',
      expiresAt: DateTime.utc(2030),
      user: UserProfile.fromJson(const {
        'id': 1,
        'username': 'dev_user',
        'display_name': 'Developer',
        'email': null,
        'auth_source': 'LOCAL',
        'last_login_at': '2026-09-24T10:00:00Z',
        'modules': [
          {
            'code': 'UPI',
            'name': 'UPI',
            'is_enabled': true,
            'roles': ['MAKER'],
            'permissions': ['dispute.view', 'dispute.act'],
          },
        ],
      }),
    );
