import 'package:json_annotation/json_annotation.dart';

part 'message.g.dart';

/// Represents a single message in a conversation
@JsonSerializable()
class Message {
  final String id;
  
  @JsonKey(name: 'conversation_id')
  final String conversationId;
  
  final String role;
  final String content;
  
  @JsonKey(name: 'created_at')
  final DateTime timestamp;
  
  @JsonKey(defaultValue: [])
  final List<FileAttachment> files;
  
  @JsonKey(name: 'audio_url')
  final String? audioUrl;
  
  @JsonKey(name: 'audio_transcription')
  final String? audioTranscription;
  
  @JsonKey(name: 'original_content')
  final String? originalContent;
  
  // Additional fields from API
  @JsonKey(name: 'model_used')
  final String? modelUsed;
  
  @JsonKey(name: 'token_count')
  final int? tokenCount;
  
  @JsonKey(name: 'tool_executions', defaultValue: [])
  final List<dynamic> toolExecutions;

  const Message({
    required this.id,
    required this.conversationId,
    required this.role,
    required this.content,
    required this.timestamp,
    this.files = const [],
    this.audioUrl,
    this.audioTranscription,
    this.originalContent,
    this.modelUsed,
    this.tokenCount,
    this.toolExecutions = const [],
  });

  factory Message.fromJson(Map<String, dynamic> json) =>
      _$MessageFromJson(json);

  Map<String, dynamic> toJson() => _$MessageToJson(this);

  // Custom getters
  bool get isUserMessage => role == 'user';
  bool get isAssistantMessage => role == 'assistant';
  bool get hasFiles => files.isNotEmpty;
  bool get hasAudio => audioUrl != null;
  bool get wasEdited => originalContent != null;

  Message copyWith({
    String? id,
    String? conversationId,
    String? role,
    String? content,
    DateTime? timestamp,
    List<FileAttachment>? files,
    String? audioUrl,
    String? audioTranscription,
    String? originalContent,
    String? modelUsed,
    int? tokenCount,
    List<dynamic>? toolExecutions,
  }) =>
      Message(
        id: id ?? this.id,
        conversationId: conversationId ?? this.conversationId,
        role: role ?? this.role,
        content: content ?? this.content,
        timestamp: timestamp ?? this.timestamp,
        files: files ?? this.files,
        audioUrl: audioUrl ?? this.audioUrl,
        audioTranscription: audioTranscription ?? this.audioTranscription,
        originalContent: originalContent ?? this.originalContent,
        modelUsed: modelUsed ?? this.modelUsed,
        tokenCount: tokenCount ?? this.tokenCount,
        toolExecutions: toolExecutions ?? this.toolExecutions,
      );

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Message &&
          runtimeType == other.runtimeType &&
          id == other.id &&
          conversationId == other.conversationId &&
          role == other.role &&
          content == other.content &&
          timestamp == other.timestamp &&
          files == other.files &&
          audioUrl == other.audioUrl &&
          audioTranscription == other.audioTranscription &&
          originalContent == other.originalContent &&
          modelUsed == other.modelUsed &&
          tokenCount == other.tokenCount;

  @override
  int get hashCode =>
      id.hashCode ^
      conversationId.hashCode ^
      role.hashCode ^
      content.hashCode ^
      timestamp.hashCode ^
      files.hashCode ^
      audioUrl.hashCode ^
      audioTranscription.hashCode ^
      originalContent.hashCode ^
      modelUsed.hashCode ^
      tokenCount.hashCode;

  @override
  String toString() =>
      'Message(id: $id, conversationId: $conversationId, role: $role, content: $content, timestamp: $timestamp, files: $files, audioUrl: $audioUrl, audioTranscription: $audioTranscription, originalContent: $originalContent, modelUsed: $modelUsed, tokenCount: $tokenCount)';
}

/// File attachment in a message
@JsonSerializable()
class FileAttachment {
  final String id;
  final String filename;
  
  @JsonKey(name: 'mime_type')
  final String mimeType;
  
  @JsonKey(name: 'size_bytes')
  final int sizeBytes;
  
  final String? url;
  final String status;
  
  @JsonKey(name: 'upload_progress')
  final double? uploadProgress;

  const FileAttachment({
    required this.id,
    required this.filename,
    required this.mimeType,
    required this.sizeBytes,
    this.url,
    this.status = 'uploaded',
    this.uploadProgress,
  });

  factory FileAttachment.fromJson(Map<String, dynamic> json) =>
      _$FileAttachmentFromJson(json);

  Map<String, dynamic> toJson() => _$FileAttachmentToJson(this);

  // Custom getters
  bool get isImage => mimeType.startsWith('image/');
  bool get isPdf => mimeType == 'application/pdf';
  bool get isWord =>
      mimeType.contains('word') || mimeType.contains('document');
  bool get isUploading => status == 'uploading';
  bool get isUploaded => status == 'uploaded';
  bool get isFailed => status == 'failed';

  FileAttachment copyWith({
    String? id,
    String? filename,
    String? mimeType,
    int? sizeBytes,
    String? url,
    String? status,
    double? uploadProgress,
  }) =>
      FileAttachment(
        id: id ?? this.id,
        filename: filename ?? this.filename,
        mimeType: mimeType ?? this.mimeType,
        sizeBytes: sizeBytes ?? this.sizeBytes,
        url: url ?? this.url,
        status: status ?? this.status,
        uploadProgress: uploadProgress ?? this.uploadProgress,
      );

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is FileAttachment &&
          runtimeType == other.runtimeType &&
          id == other.id &&
          filename == other.filename &&
          mimeType == other.mimeType &&
          sizeBytes == other.sizeBytes &&
          url == other.url &&
          status == other.status &&
          uploadProgress == other.uploadProgress;

  @override
  int get hashCode =>
      id.hashCode ^
      filename.hashCode ^
      mimeType.hashCode ^
      sizeBytes.hashCode ^
      url.hashCode ^
      status.hashCode ^
      uploadProgress.hashCode;

  @override
  String toString() =>
      'FileAttachment(id: $id, filename: $filename, mimeType: $mimeType, sizeBytes: $sizeBytes, url: $url, status: $status, uploadProgress: $uploadProgress)';
}

/// Request to send a message
@JsonSerializable()
class SendMessageRequest {
  final String conversationId;
  final String message;
  final List<String>? fileIds;
  final String? audioUrl;
  final String? audioTranscription;

  const SendMessageRequest({
    required this.conversationId,
    required this.message,
    this.fileIds,
    this.audioUrl,
    this.audioTranscription,
  });

  factory SendMessageRequest.fromJson(Map<String, dynamic> json) =>
      _$SendMessageRequestFromJson(json);

  Map<String, dynamic> toJson() => _$SendMessageRequestToJson(this);

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is SendMessageRequest &&
          runtimeType == other.runtimeType &&
          conversationId == other.conversationId &&
          message == other.message &&
          fileIds == other.fileIds &&
          audioUrl == other.audioUrl &&
          audioTranscription == other.audioTranscription;

  @override
  int get hashCode =>
      conversationId.hashCode ^
      message.hashCode ^
      fileIds.hashCode ^
      audioUrl.hashCode ^
      audioTranscription.hashCode;

  @override
  String toString() =>
      'SendMessageRequest(conversationId: $conversationId, message: $message, fileIds: $fileIds, audioUrl: $audioUrl, audioTranscription: $audioTranscription)';
}

/// Response containing conversation messages
@JsonSerializable()
class MessagesResponse {
  final String conversationId;
  final List<Message> messages;
  final int totalCount;
  final int page;
  final int pageSize;

  const MessagesResponse({
    required this.conversationId,
    required this.messages,
    required this.totalCount,
    required this.page,
    required this.pageSize,
  });

  factory MessagesResponse.fromJson(Map<String, dynamic> json) =>
      _$MessagesResponseFromJson(json);

  Map<String, dynamic> toJson() => _$MessagesResponseToJson(this);

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is MessagesResponse &&
          runtimeType == other.runtimeType &&
          conversationId == other.conversationId &&
          messages == other.messages &&
          totalCount == other.totalCount &&
          page == other.page &&
          pageSize == other.pageSize;

  @override
  int get hashCode =>
      conversationId.hashCode ^
      messages.hashCode ^
      totalCount.hashCode ^
      page.hashCode ^
      pageSize.hashCode;

  @override
  String toString() =>
      'MessagesResponse(conversationId: $conversationId, messages: $messages, totalCount: $totalCount, page: $page, pageSize: $pageSize)';
}
