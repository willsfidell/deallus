import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';

import '../providers/auth_provider.dart';

/// Authentication screen for onboarding
class AuthScreen extends ConsumerStatefulWidget {
  const AuthScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends ConsumerState<AuthScreen> {
  late TextEditingController _apiKeyController;
  late TextEditingController _apiUrlController;
  String? _errorMessage;
  bool _isValidating = false;
  final Logger _logger = Logger();

  @override
  void initState() {
    super.initState();
    _apiKeyController = TextEditingController();
    _apiUrlController = TextEditingController(text: 'http://localhost:8000');
  }

  @override
  void dispose() {
    _apiKeyController.dispose();
    _apiUrlController.dispose();
    super.dispose();
  }

  /// Validate and set credentials
  Future<void> _handleContinue() async {
    if (_apiKeyController.text.isEmpty) {
      setState(() {
        _errorMessage = 'API Key is required';
      });
      return;
    }

    if (_apiUrlController.text.isEmpty) {
      setState(() {
        _errorMessage = 'API URL is required';
      });
      return;
    }

    try {
      setState(() {
        _isValidating = true;
        _errorMessage = null;
      });

      // Use the setApiCredentialsProvider instead of notifier
      await ref.read(setApiCredentialsProvider((
        _apiKeyController.text,
        _apiUrlController.text,
      )).future);

      _logger.d('Authentication successful');

      if (mounted) {
        // Navigate to main screen - this will be handled by router
        // based on the authProvider state
      }
    } catch (e) {
      _logger.e('Authentication failed', error: e);
      setState(() {
        _errorMessage = 'Failed to authenticate: $e';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isValidating = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);

    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          child: Container(
            constraints: const BoxConstraints(maxWidth: 500),
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Logo / Title
                const Icon(
                  Icons.smart_toy,
                  size: 80,
                  color: Colors.blue,
                ),
                const SizedBox(height: 24),

                const Text(
                  'Deallus AI',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),

                const Text(
                  'AI Orchestrator Desktop Client',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey,
                  ),
                ),
                const SizedBox(height: 48),

                // Form Content
                authState.maybeWhen(
                  data: (_) => Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // API URL Input
                      TextField(
                        controller: _apiUrlController,
                        decoration: InputDecoration(
                          labelText: 'API URL',
                          hintText: 'http://localhost:8000',
                          prefixIcon: const Icon(Icons.link),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        keyboardType: TextInputType.url,
                        enabled: !_isValidating,
                      ),
                      const SizedBox(height: 16),

                      // API Key Input
                      TextField(
                        controller: _apiKeyController,
                        decoration: InputDecoration(
                          labelText: 'API Key',
                          hintText: 'Enter your API key',
                          prefixIcon: const Icon(Icons.vpn_key),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        obscureText: true,
                        enabled: !_isValidating,
                      ),
                      const SizedBox(height: 24),

                      // Error Message
                      if (_errorMessage != null)
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.red.shade50,
                            border: Border.all(color: Colors.red.shade200),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.error, color: Colors.red),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  _errorMessage!,
                                  style: const TextStyle(color: Colors.red),
                                ),
                              ),
                            ],
                          ),
                        ),
                      const SizedBox(height: 24),

                      // Continue Button
                      ElevatedButton(
                        onPressed: _isValidating ? null : _handleContinue,
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                        ),
                        child: _isValidating
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                            : const Text(
                                'Continue',
                                style: TextStyle(fontSize: 16),
                              ),
                      ),
                    ],
                  ),
                  loading: () => const Center(
                    child: CircularProgressIndicator(),
                  ),
                  error: (error, st) => Center(
                    child: Column(
                      children: [
                        const Icon(Icons.error, color: Colors.red, size: 48),
                        const SizedBox(height: 16),
                        Text('Error: $error'),
                      ],
                    ),
                  ),
                  orElse: () => const SizedBox(),
                ),

                const SizedBox(height: 24),

                // Help text
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    border: Border.all(color: Colors.blue.shade200),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.info,
                        color: Colors.blue.shade700,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Your API key is stored securely and never sent to third parties.',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.blue.shade700,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
