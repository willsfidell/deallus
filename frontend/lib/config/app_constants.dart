/// App-wide constants and configuration
class AppConstants {
  // API Configuration
  static const String defaultApiUrl = 'http://localhost:8000';
  static const Duration apiTimeout = Duration(seconds: 300); // 5 minutes for LLM processing + summarization
  static const String apiKeyHeader = 'X-API-Key';

  // Audio Recording
  static const int audioSampleRate = 16000; // Hz (16kHz for Whisper)
  static const int audioMaxDuration = 120; // seconds (2 minutes)
  static const String audioMimeType = 'audio/wav';

  // File Upload
  static const int maxFileSize = 5 * 1024 * 1024; // 5MB
  static const int maxFilesPerMessage = 4;
  static const List<String> allowedMimeTypes = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'application/pdf',
    'application/msword', // .doc
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
  ];

  // Message Caching
  static const int maxCachedMessages = 500;
  static const int messagePaginationSize = 20;

  // UI
  static const double minFontSize = 8.0;
  static const double maxFontSize = 18.0;
  static const double defaultFontSize = 14.0;

  // Storage Keys
  static const String apiKeyStorageKey = 'deallus_api_key';
  static const String apiUrlStorageKey = 'deallus_api_url';
  static const String themeStorageKey = 'deallus_theme';
  static const String fontSizeStorageKey = 'deallus_font_size';

  // Hive Database
  static const String hiveBoxName = 'deallus_cache';
}

/// API Endpoints
class ApiEndpoints {
  static const String health = '/api/health';
  static const String process = '/api/process';
  static const String conversations = '/api/conversations';
  static const String messages = '/api/conversations/{id}/messages';
}
