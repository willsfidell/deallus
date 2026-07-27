import 'package:json_annotation/json_annotation.dart';

part 'audio_recording.g.dart';

/// Audio recording metadata and state
@JsonSerializable()
class AudioRecording {
  final String id;
  final String filePath;
  final Duration duration;
  final String status;
  final double? uploadProgress;
  final String? transcription;
  final String? error;

  const AudioRecording({
    required this.id,
    required this.filePath,
    required this.duration,
    this.status = 'pending',
    this.uploadProgress,
    this.transcription,
    this.error,
  });

  factory AudioRecording.fromJson(Map<String, dynamic> json) =>
      _$AudioRecordingFromJson(json);

  Map<String, dynamic> toJson() => _$AudioRecordingToJson(this);

  // Custom getters
  bool get isRecording => status == 'recording';
  bool get isPending => status == 'pending';
  bool get isUploading => status == 'uploading';
  bool get isUploaded => status == 'uploaded';
  bool get isFailed => status == 'failed';

  int get durationSeconds => duration.inSeconds;
  String get formattedDuration {
    final minutes = durationSeconds ~/ 60;
    final seconds = durationSeconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  AudioRecording copyWith({
    String? id,
    String? filePath,
    Duration? duration,
    String? status,
    double? uploadProgress,
    String? transcription,
    String? error,
  }) =>
      AudioRecording(
        id: id ?? this.id,
        filePath: filePath ?? this.filePath,
        duration: duration ?? this.duration,
        status: status ?? this.status,
        uploadProgress: uploadProgress ?? this.uploadProgress,
        transcription: transcription ?? this.transcription,
        error: error ?? this.error,
      );

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is AudioRecording &&
          runtimeType == other.runtimeType &&
          id == other.id &&
          filePath == other.filePath &&
          duration == other.duration &&
          status == other.status &&
          uploadProgress == other.uploadProgress &&
          transcription == other.transcription &&
          error == other.error;

  @override
  int get hashCode =>
      id.hashCode ^
      filePath.hashCode ^
      duration.hashCode ^
      status.hashCode ^
      uploadProgress.hashCode ^
      transcription.hashCode ^
      error.hashCode;

  @override
  String toString() =>
      'AudioRecording(id: $id, filePath: $filePath, duration: $duration, status: $status, uploadProgress: $uploadProgress, transcription: $transcription, error: $error)';
}

/// Cached message for local storage (Hive)
@JsonSerializable()
class CachedMessage {
  final String id;
  final String conversationId;
  final String role;
  final String content;
  final DateTime timestamp;
  final List<String> fileIds;
  final String? audioUrl;
  final String? originalContent;

  const CachedMessage({
    required this.id,
    required this.conversationId,
    required this.role,
    required this.content,
    required this.timestamp,
    this.fileIds = const [],
    this.audioUrl,
    this.originalContent,
  });

  factory CachedMessage.fromJson(Map<String, dynamic> json) =>
      _$CachedMessageFromJson(json);

  Map<String, dynamic> toJson() => _$CachedMessageToJson(this);

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is CachedMessage &&
          runtimeType == other.runtimeType &&
          id == other.id &&
          conversationId == other.conversationId &&
          role == other.role &&
          content == other.content &&
          timestamp == other.timestamp &&
          fileIds == other.fileIds &&
          audioUrl == other.audioUrl &&
          originalContent == other.originalContent;

  @override
  int get hashCode =>
      id.hashCode ^
      conversationId.hashCode ^
      role.hashCode ^
      content.hashCode ^
      timestamp.hashCode ^
      fileIds.hashCode ^
      audioUrl.hashCode ^
      originalContent.hashCode;

  @override
  String toString() =>
      'CachedMessage(id: $id, conversationId: $conversationId, role: $role, content: $content, timestamp: $timestamp, fileIds: $fileIds, audioUrl: $audioUrl, originalContent: $originalContent)';
}
