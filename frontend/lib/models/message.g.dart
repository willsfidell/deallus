// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'message.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Message _$MessageFromJson(Map<String, dynamic> json) => Message(
      id: json['id'] as String,
      conversationId: json['conversation_id'] as String,
      role: json['role'] as String,
      content: json['content'] as String,
      timestamp: DateTime.parse(json['created_at'] as String),
      files: (json['files'] as List<dynamic>?)
              ?.map((e) => FileAttachment.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      audioUrl: json['audio_url'] as String?,
      audioTranscription: json['audio_transcription'] as String?,
      originalContent: json['original_content'] as String?,
      modelUsed: json['model_used'] as String?,
      tokenCount: (json['token_count'] as num?)?.toInt(),
      toolExecutions: json['tool_executions'] as List<dynamic>? ?? [],
    );

Map<String, dynamic> _$MessageToJson(Message instance) => <String, dynamic>{
      'id': instance.id,
      'conversation_id': instance.conversationId,
      'role': instance.role,
      'content': instance.content,
      'created_at': instance.timestamp.toIso8601String(),
      'files': instance.files,
      'audio_url': instance.audioUrl,
      'audio_transcription': instance.audioTranscription,
      'original_content': instance.originalContent,
      'model_used': instance.modelUsed,
      'token_count': instance.tokenCount,
      'tool_executions': instance.toolExecutions,
    };

FileAttachment _$FileAttachmentFromJson(Map<String, dynamic> json) =>
    FileAttachment(
      id: json['id'] as String,
      filename: json['filename'] as String,
      mimeType: json['mime_type'] as String,
      sizeBytes: (json['size_bytes'] as num).toInt(),
      url: json['url'] as String?,
      status: json['status'] as String? ?? 'uploaded',
      uploadProgress: (json['upload_progress'] as num?)?.toDouble(),
    );

Map<String, dynamic> _$FileAttachmentToJson(FileAttachment instance) =>
    <String, dynamic>{
      'id': instance.id,
      'filename': instance.filename,
      'mime_type': instance.mimeType,
      'size_bytes': instance.sizeBytes,
      'url': instance.url,
      'status': instance.status,
      'upload_progress': instance.uploadProgress,
    };

SendMessageRequest _$SendMessageRequestFromJson(Map<String, dynamic> json) =>
    SendMessageRequest(
      conversationId: json['conversationId'] as String,
      message: json['message'] as String,
      fileIds:
          (json['fileIds'] as List<dynamic>?)?.map((e) => e as String).toList(),
      audioUrl: json['audioUrl'] as String?,
      audioTranscription: json['audioTranscription'] as String?,
    );

Map<String, dynamic> _$SendMessageRequestToJson(SendMessageRequest instance) =>
    <String, dynamic>{
      'conversationId': instance.conversationId,
      'message': instance.message,
      'fileIds': instance.fileIds,
      'audioUrl': instance.audioUrl,
      'audioTranscription': instance.audioTranscription,
    };

MessagesResponse _$MessagesResponseFromJson(Map<String, dynamic> json) =>
    MessagesResponse(
      conversationId: json['conversationId'] as String,
      messages: (json['messages'] as List<dynamic>)
          .map((e) => Message.fromJson(e as Map<String, dynamic>))
          .toList(),
      totalCount: (json['totalCount'] as num).toInt(),
      page: (json['page'] as num).toInt(),
      pageSize: (json['pageSize'] as num).toInt(),
    );

Map<String, dynamic> _$MessagesResponseToJson(MessagesResponse instance) =>
    <String, dynamic>{
      'conversationId': instance.conversationId,
      'messages': instance.messages,
      'totalCount': instance.totalCount,
      'page': instance.page,
      'pageSize': instance.pageSize,
    };
