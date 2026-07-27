import 'package:json_annotation/json_annotation.dart';

part 'settings.g.dart';

/// Application theme mode options
enum AppThemeMode {
  @JsonValue('light')
  light,
  @JsonValue('dark')
  dark,
  @JsonValue('auto')
  auto,
}

/// User application settings
@JsonSerializable()
class AppSettings {
  final String apiUrl;
  final String apiKey;
  final AppThemeMode theme;
  final double fontSize;
  final bool saveMessagesLocally;
  final int maxCacheMessages;

  const AppSettings({
    required this.apiUrl,
    required this.apiKey,
    this.theme = AppThemeMode.auto,
    this.fontSize = 14.0,
    this.saveMessagesLocally = true,
    this.maxCacheMessages = 500,
  });

  factory AppSettings.fromJson(Map<String, dynamic> json) =>
      _$AppSettingsFromJson(json);

  Map<String, dynamic> toJson() => _$AppSettingsToJson(this);

  // Custom getters
  bool get hasValidApiKey => apiKey.isNotEmpty;
  bool get hasValidApiUrl => apiUrl.isNotEmpty;
  bool get isConfigured => hasValidApiKey && hasValidApiUrl;

  // Manual copyWith
  AppSettings copyWith({
    String? apiUrl,
    String? apiKey,
    AppThemeMode? theme,
    double? fontSize,
    bool? saveMessagesLocally,
    int? maxCacheMessages,
  }) =>
      AppSettings(
        apiUrl: apiUrl ?? this.apiUrl,
        apiKey: apiKey ?? this.apiKey,
        theme: theme ?? this.theme,
        fontSize: fontSize ?? this.fontSize,
        saveMessagesLocally: saveMessagesLocally ?? this.saveMessagesLocally,
        maxCacheMessages: maxCacheMessages ?? this.maxCacheMessages,
      );

  AppSettings copyWithUpdatedUrl(String newUrl) => copyWith(apiUrl: newUrl);
  AppSettings copyWithUpdatedKey(String newKey) => copyWith(apiKey: newKey);

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is AppSettings &&
          runtimeType == other.runtimeType &&
          apiUrl == other.apiUrl &&
          apiKey == other.apiKey &&
          theme == other.theme &&
          fontSize == other.fontSize &&
          saveMessagesLocally == other.saveMessagesLocally &&
          maxCacheMessages == other.maxCacheMessages;

  @override
  int get hashCode =>
      apiUrl.hashCode ^
      apiKey.hashCode ^
      theme.hashCode ^
      fontSize.hashCode ^
      saveMessagesLocally.hashCode ^
      maxCacheMessages.hashCode;

  @override
  String toString() =>
      'AppSettings(apiUrl: $apiUrl, apiKey: $apiKey, theme: $theme, fontSize: $fontSize, saveMessagesLocally: $saveMessagesLocally, maxCacheMessages: $maxCacheMessages)';
}
