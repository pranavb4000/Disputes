import 'package:dms_web/core/network/api_exception.dart';
import 'package:dms_web/core/theme/app_theme.dart';
import 'package:dms_web/features/auth/data/auth_repository.dart';
import 'package:dms_web/features/auth/presentation/login_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'helpers.dart';

Widget _wrap(AuthRepository repository) => ProviderScope(
      overrides: [authRepositoryProvider.overrideWithValue(repository)],
      child: MaterialApp(theme: AppTheme.light(), home: const LoginPage()),
    );

void main() {
  late MockAuthRepository repository;

  setUp(() => repository = MockAuthRepository());

  testWidgets('shows validation messages when fields are empty', (tester) async {
    await tester.pumpWidget(_wrap(repository));

    await tester.tap(find.byKey(const Key('login-submit')));
    await tester.pump();

    expect(find.text('Enter your username'), findsOneWidget);
    expect(find.text('Enter your password'), findsOneWidget);
    verifyNever(() => repository.login(any(), any()));
  });

  testWidgets('submits credentials', (tester) async {
    when(() => repository.login('dev_user', 'secret-pass')).thenAnswer((_) async => sampleSession());
    await tester.pumpWidget(_wrap(repository));

    await tester.enterText(find.byKey(const Key('login-username')), 'dev_user');
    await tester.enterText(find.byKey(const Key('login-password')), 'secret-pass');
    await tester.tap(find.byKey(const Key('login-submit')));
    await tester.pumpAndSettle();

    verify(() => repository.login('dev_user', 'secret-pass')).called(1);
  });

  testWidgets('shows the server error message on failure', (tester) async {
    when(() => repository.login(any(), any())).thenThrow(
      const ApiException('Invalid username or password', statusCode: 401),
    );
    await tester.pumpWidget(_wrap(repository));

    await tester.enterText(find.byKey(const Key('login-username')), 'dev_user');
    await tester.enterText(find.byKey(const Key('login-password')), 'wrong');
    await tester.tap(find.byKey(const Key('login-submit')));
    await tester.pumpAndSettle();

    expect(find.text('Invalid username or password'), findsOneWidget);
  });
}
