// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'message.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Message _$MessageFromJson(Map<String, dynamic> json) => Message(
      id: json['id'] as String,
      conversationId: json['conversationId'] as String,
      role: json['role'] as String,
      content: json['content'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
      files: (json['files'] as List<dynamic>?)
              ?.map((e) => FileAttachment.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      audioUrl: json['audioUrl'] as String?,
      audioTranscription: json['audioTranscription'] as String?,
      originalContent: json['originalContent'] as String?,
    );

Map<String, dynamic> _$MessageToJson(Message instance) => <String, dynamic>{
      'id': instance.id,
      'conversationId': instance.conversationId,
      'role': instance.role,
      'content': instance.content,
      'timestamp': instance.timestamp.toIso8601String(),
      'files': instance.files,
      'audioUrl': instance.audioUrl,
      'audioTranscription': instance.audioTranscription,
      'originalContent': instance.originalContent,
    };

FileAttachment _$FileAttachmentFromJson(Map<String, dynamic> json) =>
    FileAttachment(
      id: json['id'] as String,
      filename: json['filename'] as String,
      mimeType: json['mimeType'] as String,
      sizeBytes: (json['sizeBytes'] as num).toInt(),
      url: json['url'] as String?,
      status: json['status'] as String? ?? 'uploaded',
      uploadProgress: (json['uploadProgress'] as num?)?.toDouble(),
    );

Map<String, dynamic> _$FileAttachmentToJson(FileAttachment instance) =>
    <String, dynamic>{
      'id': instance.id,
      'filename': instance.filename,
      'mimeType': instance.mimeType,
      'sizeBytes': instance.sizeBytes,
      'url': instance.url,
      'status': instance.status,
      'uploadProgress': instance.uploadProgress,
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
