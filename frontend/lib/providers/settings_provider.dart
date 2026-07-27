import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';

import '../config/app_constants.dart';
import '../models/exceptions.dart';
import '../models/settings.dart';
import '../services/secure_storage_service.dart';

final _logger = Logger();

/// Provider for SecureStorageService (singleton)
final secureStorageProvider = Provider<SecureStorageService>((ref) {
  return SecureStorageService();
});

/// Helper: Parse theme string to AppThemeMode
AppThemeMode _parseTheme(String themeStr) {
  switch (themeStr.toLowerCase()) {
    case 'light':
      return AppThemeMode.light;
    case 'dark':
      return AppThemeMode.dark;
    case 'auto':
    default:
      return AppThemeMode.auto;
  }
}

/// Helper: Convert AppThemeMode to string
String _themeToString(AppThemeMode theme) {
  switch (theme) {
    case AppThemeMode.light:
      return 'light';
    case AppThemeMode.dark:
      return 'dark';
    case AppThemeMode.auto:
      return 'auto';
  }
}

/// Provider for app settings state (simple FutureProvider)
final settingsProvider = FutureProvider<AppSettings>((ref) async {
  final storage = ref.watch(secureStorageProvider);
  
  try {
    final apiUrl = await storage.getApiUrl() ?? AppConstants.defaultApiUrl;
    final apiKey = await storage.getApiKey() ?? '';
    final themeStr = await storage.getTheme() ?? 'auto';
    final fontSize = await storage.getFontSize() ?? AppConstants.defaultFontSize;

    final theme = _parseTheme(themeStr);

    return AppSettings(
      apiUrl: apiUrl,
      apiKey: apiKey,
      theme: theme,
      fontSize: fontSize,
    );
  } catch (e, st) {
    _logger.e('Failed to load settings', error: e, stackTrace: st);
    
    // Return default settings on error
    return AppSettings(
      apiUrl: AppConstants.defaultApiUrl,
      apiKey: '',
    );
  }
});

/// Family provider for updating settings
final updateSettingsProvider = FutureProvider.family<void, AppSettings>((ref, settings) async {
  final storage = ref.watch(secureStorageProvider);
  
  try {
    await storage.saveApiUrl(settings.apiUrl);
    await storage.saveApiKey(settings.apiKey);
    await storage.saveTheme(_themeToString(settings.theme));
    await storage.saveFontSize(settings.fontSize);
    
    _logger.d('Settings saved');
    
    // Invalidate the main settings provider to refresh
    ref.invalidate(settingsProvider);
  } catch (e, st) {
    _logger.e('Failed to save settings', error: e, stackTrace: st);
    rethrow;
  }
});

/// Provider for theme mode
final themeProvider = Provider<AppThemeMode>((ref) {
  final settings = ref.watch(settingsProvider);
  return settings.maybeWhen(
    data: (s) => s.theme,
    orElse: () => AppThemeMode.auto,
  );
});

/// Provider for font size
final fontSizeProvider = Provider<double>((ref) {
  final settings = ref.watch(settingsProvider);
  return settings.maybeWhen(
    data: (s) => s.fontSize,
    orElse: () => AppConstants.defaultFontSize,
  );
});
