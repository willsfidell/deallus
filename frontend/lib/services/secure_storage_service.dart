import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:logger/logger.dart';

import '../models/exceptions.dart';
import '../config/app_constants.dart';

/// Service for secure storage of sensitive data
class SecureStorageService {
  static const _instance = FlutterSecureStorage(
    aOptions: AndroidOptions(
      keyCipherAlgorithm: KeyCipherAlgorithm.RSA_ECB_OAEPwithSHA_256andMGF1Padding,
      storageCipherAlgorithm: StorageCipherAlgorithm.AES_GCM_NoPadding,
    ),
  );

  final Logger _logger = Logger();

  /// Save API key securely
  Future<void> saveApiKey(String apiKey) async {
    try {
      await _instance.write(
        key: AppConstants.apiKeyStorageKey,
        value: apiKey,
      );
      _logger.d('API key saved securely');
    } catch (e) {
      _logger.e('Failed to save API key', error: e);
      throw StorageException(
        message: 'Failed to save API key: $e',
        originalException: e,
      );
    }
  }

  /// Retrieve API key from secure storage
  Future<String?> getApiKey() async {
    try {
      final apiKey = await _instance.read(
        key: AppConstants.apiKeyStorageKey,
      );
      return apiKey;
    } catch (e) {
      _logger.e('Failed to retrieve API key', error: e);
      throw StorageException(
        message: 'Failed to retrieve API key: $e',
        originalException: e,
      );
    }
  }

  /// Save API endpoint URL
  Future<void> saveApiUrl(String apiUrl) async {
    try {
      await _instance.write(
        key: AppConstants.apiUrlStorageKey,
        value: apiUrl,
      );
      _logger.d('API URL saved');
    } catch (e) {
      _logger.e('Failed to save API URL', error: e);
      throw StorageException(
        message: 'Failed to save API URL: $e',
        originalException: e,
      );
    }
  }

  /// Retrieve API endpoint URL
  Future<String?> getApiUrl() async {
    try {
      final url = await _instance.read(
        key: AppConstants.apiUrlStorageKey,
      );
      return url;
    } catch (e) {
      _logger.e('Failed to retrieve API URL', error: e);
      throw StorageException(
        message: 'Failed to retrieve API URL: $e',
        originalException: e,
      );
    }
  }

  /// Save theme preference
  Future<void> saveTheme(String theme) async {
    try {
      await _instance.write(
        key: AppConstants.themeStorageKey,
        value: theme,
      );
      _logger.d('Theme saved: $theme');
    } catch (e) {
      _logger.e('Failed to save theme', error: e);
      throw StorageException(
        message: 'Failed to save theme: $e',
        originalException: e,
      );
    }
  }

  /// Retrieve theme preference
  Future<String?> getTheme() async {
    try {
      return await _instance.read(
        key: AppConstants.themeStorageKey,
      );
    } catch (e) {
      _logger.e('Failed to retrieve theme', error: e);
      throw StorageException(
        message: 'Failed to retrieve theme: $e',
        originalException: e,
      );
    }
  }

  /// Save font size preference
  Future<void> saveFontSize(double fontSize) async {
    try {
      await _instance.write(
        key: AppConstants.fontSizeStorageKey,
        value: fontSize.toString(),
      );
      _logger.d('Font size saved: $fontSize');
    } catch (e) {
      _logger.e('Failed to save font size', error: e);
      throw StorageException(
        message: 'Failed to save font size: $e',
        originalException: e,
      );
    }
  }

  /// Retrieve font size preference
  Future<double?> getFontSize() async {
    try {
      final value = await _instance.read(
        key: AppConstants.fontSizeStorageKey,
      );
      return value != null ? double.tryParse(value) : null;
    } catch (e) {
      _logger.e('Failed to retrieve font size', error: e);
      throw StorageException(
        message: 'Failed to retrieve font size: $e',
        originalException: e,
      );
    }
  }

  /// Clear all stored data (on logout)
  Future<void> clearAll() async {
    try {
      await _instance.deleteAll();
      _logger.d('All secure storage cleared');
    } catch (e) {
      _logger.e('Failed to clear secure storage', error: e);
      throw StorageException(
        message: 'Failed to clear storage: $e',
        originalException: e,
      );
    }
  }

  /// Delete specific key
  Future<void> delete(String key) async {
    try {
      await _instance.delete(key: key);
      _logger.d('Storage key deleted: $key');
    } catch (e) {
      _logger.e('Failed to delete storage key', error: e);
      throw StorageException(
        message: 'Failed to delete storage key: $e',
        originalException: e,
      );
    }
  }
}
