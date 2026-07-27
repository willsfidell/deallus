// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'settings.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AppSettings _$AppSettingsFromJson(Map<String, dynamic> json) => AppSettings(
      apiUrl: json['apiUrl'] as String,
      apiKey: json['apiKey'] as String,
      theme: $enumDecodeNullable(_$AppThemeModeEnumMap, json['theme']) ??
          AppThemeMode.auto,
      fontSize: (json['fontSize'] as num?)?.toDouble() ?? 14.0,
      saveMessagesLocally: json['saveMessagesLocally'] as bool? ?? true,
      maxCacheMessages: (json['maxCacheMessages'] as num?)?.toInt() ?? 500,
    );

Map<String, dynamic> _$AppSettingsToJson(AppSettings instance) =>
    <String, dynamic>{
      'apiUrl': instance.apiUrl,
      'apiKey': instance.apiKey,
      'theme': _$AppThemeModeEnumMap[instance.theme]!,
      'fontSize': instance.fontSize,
      'saveMessagesLocally': instance.saveMessagesLocally,
      'maxCacheMessages': instance.maxCacheMessages,
    };

const _$AppThemeModeEnumMap = {
  AppThemeMode.light: 'light',
  AppThemeMode.dark: 'dark',
  AppThemeMode.auto: 'auto',
};
