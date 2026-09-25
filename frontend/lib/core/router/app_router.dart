import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/application/auth_controller.dart';
import '../../features/auth/presentation/login_page.dart';
import '../../features/auth/presentation/splash_page.dart';
import '../../features/home/presentation/home_page.dart';
import '../../shared/widgets/not_found_page.dart';

abstract final class AppRoutes {
  static const String splash = '/';
  static const String login = '/login';
  static const String home = '/home';
}

/// Auth-aware routing: unknown -> splash (restoring session), logged out -> login, logged in -> app.
final routerProvider = Provider<GoRouter>((ref) {
  final authStatus = ValueNotifier<AuthStatus>(ref.read(authControllerProvider).status);
  ref.listen<AuthState>(authControllerProvider, (previous, next) => authStatus.value = next.status);
  ref.onDispose(authStatus.dispose);

  return GoRouter(
    initialLocation: AppRoutes.splash,
    refreshListenable: authStatus,
    redirect: (context, state) {
      final status = authStatus.value;
      final location = state.matchedLocation;
      switch (status) {
        case AuthStatus.unknown:
          return location == AppRoutes.splash ? null : AppRoutes.splash;
        case AuthStatus.unauthenticated:
          return location == AppRoutes.login ? null : AppRoutes.login;
        case AuthStatus.authenticated:
          return (location == AppRoutes.login || location == AppRoutes.splash) ? AppRoutes.home : null;
      }
    },
    routes: [
      GoRoute(path: AppRoutes.splash, builder: (context, state) => const SplashPage()),
      GoRoute(path: AppRoutes.login, builder: (context, state) => const LoginPage()),
      GoRoute(path: AppRoutes.home, builder: (context, state) => const HomePage()),
    ],
    errorBuilder: (context, state) => const NotFoundPage(),
  );
});
