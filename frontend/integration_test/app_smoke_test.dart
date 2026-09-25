// End-to-end smoke test against a running stack (docker compose up).
//
//   flutter drive --driver=test_driver/integration_test.dart \
//     --target=integration_test/app_smoke_test.dart -d web-server \
//     --dart-define=API_BASE_URL=http://localhost:8080 \
//     --dart-define=E2E_USERNAME=dev_user --dart-define=E2E_PASSWORD=<DEV_USER_PASSWORD>
import 'package:dms_web/app.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('log in, see the home page, log out', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: DmsApp()));
    await tester.pumpAndSettle(const Duration(seconds: 3));

    await tester.enterText(find.byKey(const Key('login-username')), const String.fromEnvironment('E2E_USERNAME'));
    await tester.enterText(find.byKey(const Key('login-password')), const String.fromEnvironment('E2E_PASSWORD'));
    await tester.tap(find.byKey(const Key('login-submit')));
    await tester.pumpAndSettle(const Duration(seconds: 3));
    expect(find.textContaining('Welcome,'), findsOneWidget);

    await tester.tap(find.byTooltip('Account'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Log out'));
    await tester.pumpAndSettle(const Duration(seconds: 2));
    expect(find.text('Sign in'), findsWidgets);
  });
}
