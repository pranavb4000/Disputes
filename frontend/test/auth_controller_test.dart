import 'package:dms_web/core/auth/token_store.dart';
import 'package:dms_web/core/network/api_exception.dart';
import 'package:dms_web/features/auth/application/auth_controller.dart';
import 'package:dms_web/features/auth/data/auth_repository.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'helpers.dart';

void main() {
  late MockAuthRepository repository;
  late ProviderContainer container;

  setUp(() {
    repository = MockAuthRepository();
    container = ProviderContainer(overrides: [authRepositoryProvider.overrideWithValue(repository)]);
  });

  tearDown(() => container.dispose());

  test('starts in the unknown state', () {
    expect(container.read(authControllerProvider).status, AuthStatus.unknown);
  });

  test('successful login stores the token in memory and exposes the user', () async {
    when(() => repository.login('dev_user', 'pw')).thenAnswer((_) async => sampleSession());

    final ok = await container.read(authControllerProvider.notifier).login('dev_user', 'pw');

    expect(ok, isTrue);
    final state = container.read(authControllerProvider);
    expect(state.status, AuthStatus.authenticated);
    expect(state.user!.can('UPI', 'dispute.view'), isTrue);
    expect(state.user!.can('UPI', 'dispute.approve'), isFalse);
    expect(container.read(tokenStoreProvider).accessToken, 'access-token');
  });

  test('failed login shows the server message and keeps the user logged out', () async {
    when(() => repository.login(any(), any())).thenThrow(
      const ApiException('Invalid username or password', errorCode: 'INVALID_CREDENTIALS', statusCode: 401),
    );

    final ok = await container.read(authControllerProvider.notifier).login('dev_user', 'bad');

    expect(ok, isFalse);
    final state = container.read(authControllerProvider);
    expect(state.status, AuthStatus.unauthenticated);
    expect(state.errorMessage, 'Invalid username or password');
    expect(container.read(tokenStoreProvider).hasToken, isFalse);
  });

  test('restoreSession without a refresh cookie goes to the login page', () async {
    when(() => repository.refresh()).thenAnswer((_) async => null);

    await container.read(authControllerProvider.notifier).restoreSession();

    expect(container.read(authControllerProvider).status, AuthStatus.unauthenticated);
  });

  test('logout clears the token and calls the server', () async {
    when(() => repository.login(any(), any())).thenAnswer((_) async => sampleSession());
    when(() => repository.logout(any())).thenAnswer((_) async {});
    final controller = container.read(authControllerProvider.notifier);
    await controller.login('dev_user', 'pw');

    await controller.logout();

    expect(container.read(authControllerProvider).status, AuthStatus.unauthenticated);
    expect(container.read(tokenStoreProvider).hasToken, isFalse);
    verify(() => repository.logout('access-token')).called(1);
  });
}
