import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';

import '../models/api_response.dart';
import '../models/exceptions.dart';
import '../models/settings.dart';
import '../services/api_service.dart';
import '../services/chat_service.dart';
import 'settings_provider.dart';

final _logger = Logger();

/// Provider for ApiService singleton
final apiServiceProvider = Provider<ApiService>((ref) {
  return ApiService();
});

/// Provider for ChatService singleton
final chatServiceProvider = Provider<ChatService>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return ChatService(apiService);
});

/// Auth state class
class AuthState {
  final String apiKey;
  final String apiUrl;
  final bool isAuthenticated;
  final String? error;

  AuthState({
    required this.apiKey,
    required this.apiUrl,
    required this.isAuthenticated,
    this.error,
  });

  AuthState copyWith({
    String? apiKey,
    String? apiUrl,
    bool? isAuthenticated,
    String? error,
  }) {
    return AuthState(
      apiKey: apiKey ?? this.apiKey,
      apiUrl: apiUrl ?? this.apiUrl,
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      error: error ?? this.error,
    );
  }
}

/// Provider for authentication state
final authProvider = FutureProvider<AuthState>((ref) async {
  final settings = ref.watch(settingsProvider);
  final apiService = ref.watch(apiServiceProvider);

  try {
    final appSettings = await settings.value;
    
    if (appSettings == null) {
      return AuthState(
        apiKey: '',
        apiUrl: '',
        isAuthenticated: false,
        error: 'Settings not loaded',
      );
    }

    // Update API service with stored credentials
    apiService.updateConfig(
      apiUrl: appSettings.apiUrl,
      apiKey: appSettings.apiKey,
    );

    // Validate the credentials if both are set
    if (appSettings.hasValidApiKey && appSettings.hasValidApiUrl) {
      final isValid = await _validateApiKey(apiService, appSettings.apiKey, appSettings.apiUrl);
      return AuthState(
        apiKey: appSettings.apiKey,
        apiUrl: appSettings.apiUrl,
        isAuthenticated: isValid,
        error: isValid ? null : 'Invalid API credentials',
      );
    } else {
      return AuthState(
        apiKey: appSettings.apiKey,
        apiUrl: appSettings.apiUrl,
        isAuthenticated: false,
      );
    }
  } catch (e, st) {
    _logger.e('Failed to initialize auth', error: e, stackTrace: st);
    rethrow;
  }
});

/// Validate API key with backend
Future<bool> _validateApiKey(
  ApiService apiService,
  String apiKey,
  String apiUrl,
) async {
  try {
    _logger.d('Validating API key with backend');

    // Temporarily update API service to validate
    apiService.updateConfig(
      apiUrl: apiUrl,
      apiKey: apiKey,
    );

    final health = await apiService.getHealth();
    final isValid = health.status.toLowerCase() == 'healthy' || 
                     health.status.toLowerCase() == 'ok';

    _logger.d('API validation result: $isValid');
    return isValid;
  } catch (e) {
    _logger.w('API validation failed', error: e);
    return false;
  }
}

/// Provider for setting API credentials
final setApiCredentialsProvider = FutureProvider.family<void, (String, String)>((ref, credentials) async {
  final (apiKey, apiUrl) = credentials;
  final apiService = ref.watch(apiServiceProvider);
  final storage = ref.watch(secureStorageProvider);

  try {
    if (apiKey.isEmpty || apiUrl.isEmpty) {
      throw ValidationException(
        message: 'API key and URL cannot be empty',
      );
    }

    // Validate format
    Uri.parse(apiUrl); // Will throw if invalid URL

    // Validate with backend
    final isValid = await _validateApiKey(apiService, apiKey, apiUrl);

    if (!isValid) {
      throw AuthException(
        message: 'Invalid API credentials - cannot reach backend',
      );
    }

    // Save to storage
    await storage.saveApiKey(apiKey);
    await storage.saveApiUrl(apiUrl);

    // Update API service config
    apiService.updateConfig(
      apiUrl: apiUrl,
      apiKey: apiKey,
    );

    _logger.d('API credentials validated and set');

    // Invalidate both settings and auth providers to refresh
    ref.invalidate(settingsProvider);
    ref.invalidate(authProvider);
  } catch (e, st) {
    _logger.e('Failed to set API credentials', error: e, stackTrace: st);
    rethrow;
  }
});

/// Provider for clearing authentication
final clearAuthProvider = FutureProvider<void>((ref) async {
  final storage = ref.watch(secureStorageProvider);

  try {
    await storage.clearAll();
    _logger.d('Authentication cleared');

    // Invalidate providers to refresh
    ref.invalidate(settingsProvider);
    ref.invalidate(authProvider);
  } catch (e, st) {
    _logger.e('Failed to clear auth', error: e, stackTrace: st);
    rethrow;
  }
});
