import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/brand_colors.dart';
import '../../../shared/widgets/brand_widgets.dart';
import '../../../shared/widgets/brand_wordmark.dart';
import '../application/auth_controller.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _username = TextEditingController();
  final _password = TextEditingController();
  bool _obscure = true;

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final ok = await ref.read(authControllerProvider.notifier).login(_username.text.trim(), _password.text);
    if (!ok && mounted) {
      _password.clear();
    }
    // On success the router redirects to /home automatically.
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final wide = MediaQuery.sizeOf(context).width >= 900;

    final form = ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 400),
      child: Form(
        key: _formKey,
        child: AutofillGroup(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Sign in',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      color: BrandColors.maroon,
                      fontWeight: FontWeight.w700,
                    ),
              ),
              const SizedBox(height: 4),
              const Text('Dispute Management System', style: TextStyle(color: BrandColors.textPrimary)),
              const SizedBox(height: 24),
              if (auth.sessionExpired) ...[
                const StatusBanner(message: 'Your session has expired. Please sign in again.'),
                const SizedBox(height: 16),
              ],
              if (auth.errorMessage != null) ...[
                StatusBanner(message: auth.errorMessage!, kind: BannerKind.error),
                const SizedBox(height: 16),
              ],
              TextFormField(
                key: const Key('login-username'),
                controller: _username,
                enabled: !auth.isBusy,
                autofocus: true,
                autofillHints: const [AutofillHints.username],
                textInputAction: TextInputAction.next,
                inputFormatters: [FilteringTextInputFormatter.deny(RegExp(r'\s'))],
                decoration: brandInputDecoration(label: 'Username', prefixIcon: const Icon(Icons.person_outline)),
                validator: (value) => (value == null || value.trim().isEmpty) ? 'Enter your username' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                key: const Key('login-password'),
                controller: _password,
                enabled: !auth.isBusy,
                obscureText: _obscure,
                autofillHints: const [AutofillHints.password],
                textInputAction: TextInputAction.done,
                onFieldSubmitted: (_) => _submit(),
                decoration: brandInputDecoration(
                  label: 'Password',
                  prefixIcon: const Icon(Icons.lock_outline),
                  suffixIcon: IconButton(
                    tooltip: _obscure ? 'Show password' : 'Hide password',
                    icon: Icon(_obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                    onPressed: () => setState(() => _obscure = !_obscure),
                  ),
                ),
                validator: (value) => (value == null || value.isEmpty) ? 'Enter your password' : null,
              ),
              const SizedBox(height: 24),
              FilledButton(
                key: const Key('login-submit'),
                onPressed: auth.isBusy ? null : _submit,
                child: auth.isBusy
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: BrandColors.white),
                      )
                    : const Text('Sign in'),
              ),
              const SizedBox(height: 24),
              const Text(
                'Authorised users only. All activity is logged and monitored.',
                textAlign: TextAlign.center,
                style: TextStyle(color: BrandColors.textPrimary, fontSize: 12),
              ),
            ],
          ),
        ),
      ),
    );

    final formPanel = Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(32),
        child: form,
      ),
    );

    if (!wide) {
      return Scaffold(
        appBar: AppBar(
          backgroundColor: BrandColors.maroon,
          foregroundColor: BrandColors.white,
          title: const BrandWordmark(size: 18),
        ),
        backgroundColor: BrandColors.white,
        body: formPanel,
      );
    }

    return Scaffold(
      backgroundColor: BrandColors.white,
      body: Row(
        children: [
          Expanded(
            flex: 5,
            child: Container(
              color: BrandColors.maroon,
              padding: const EdgeInsets.all(48),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const BrandWordmark(size: 28),
                  const Spacer(),
                  Text(
                    'Dispute Management System',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          color: BrandColors.white,
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'UPI · IMPS · AEPS · E-Toll',
                    style: TextStyle(color: BrandColors.maroonTint20, fontSize: 16),
                  ),
                  const Spacer(),
                ],
              ),
            ),
          ),
          Expanded(flex: 6, child: formPanel),
        ],
      ),
    );
  }
}
