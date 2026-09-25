import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class NotFoundPage extends StatelessWidget {
  const NotFoundPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Page not found', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 16),
            FilledButton(onPressed: () => context.go('/home'), child: const Text('Go to Home')),
          ],
        ),
      ),
    );
  }
}
