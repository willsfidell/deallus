// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'audio_recording.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AudioRecording _$AudioRecordingFromJson(Map<String, dynamic> json) =>
    AudioRecording(
      id: json['id'] as String,
      filePath: json['filePath'] as String,
      duration: Duration(microseconds: (json['duration'] as num).toInt()),
      status: json['status'] as String? ?? 'pending',
      uploadProgress: (json['uploadProgress'] as num?)?.toDouble(),
      transcription: json['transcription'] as String?,
      error: json['error'] as String?,
    );

Map<String, dynamic> _$AudioRecordingToJson(AudioRecording instance) =>
    <String, dynamic>{
      'id': instance.id,
      'filePath': instance.filePath,
      'duration': instance.duration.inMicroseconds,
      'status': instance.status,
      'uploadProgress': instance.uploadProgress,
      'transcription': instance.transcription,
      'error': instance.error,
    };

CachedMessage _$CachedMessageFromJson(Map<String, dynamic> json) =>
    CachedMessage(
      id: json['id'] as String,
      conversationId: json['conversationId'] as String,
      role: json['role'] as String,
      content: json['content'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
      fileIds: (json['fileIds'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      audioUrl: json['audioUrl'] as String?,
      originalContent: json['originalContent'] as String?,
    );

Map<String, dynamic> _$CachedMessageToJson(CachedMessage instance) =>
    <String, dynamic>{
      'id': instance.id,
      'conversationId': instance.conversationId,
      'role': instance.role,
      'content': instance.content,
      'timestamp': instance.timestamp.toIso8601String(),
      'fileIds': instance.fileIds,
      'audioUrl': instance.audioUrl,
      'originalContent': instance.originalContent,
    };
