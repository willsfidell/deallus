import 'package:json_annotation/json_annotation.dart';

part 'chat.g.dart';

/// Represents a conversation/chat
@JsonSerializable()
class Chat {
  final String id;
  final String title;
  final DateTime createdAt;
  final DateTime? updatedAt;
  final int messageCount;
  final String? lastMessagePreview;

  const Chat({
    required this.id,
    required this.title,
    required this.createdAt,
    this.updatedAt,
    required this.messageCount,
    this.lastMessagePreview,
  });

  factory Chat.fromJson(Map<String, dynamic> json) => _$ChatFromJson(json);

  Map<String, dynamic> toJson() => _$ChatToJson(this);

  Chat copyWith({
    String? id,
    String? title,
    DateTime? createdAt,
    DateTime? updatedAt,
    int? messageCount,
    String? lastMessagePreview,
  }) =>
      Chat(
        id: id ?? this.id,
        title: title ?? this.title,
        createdAt: createdAt ?? this.createdAt,
        updatedAt: updatedAt ?? this.updatedAt,
        messageCount: messageCount ?? this.messageCount,
        lastMessagePreview: lastMessagePreview ?? this.lastMessagePreview,
      );

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Chat &&
          runtimeType == other.runtimeType &&
          id == other.id &&
          title == other.title &&
          createdAt == other.createdAt &&
          updatedAt == other.updatedAt &&
          messageCount == other.messageCount &&
          lastMessagePreview == other.lastMessagePreview;

  @override
  int get hashCode =>
      id.hashCode ^
      title.hashCode ^
      createdAt.hashCode ^
      updatedAt.hashCode ^
      messageCount.hashCode ^
      lastMessagePreview.hashCode;

  @override
  String toString() =>
      'Chat(id: $id, title: $title, createdAt: $createdAt, updatedAt: $updatedAt, messageCount: $messageCount, lastMessagePreview: $lastMessagePreview)';
}

/// Request to create a new conversation
@JsonSerializable()
class CreateChatRequest {
  final String? title;

  const CreateChatRequest({this.title});

  factory CreateChatRequest.fromJson(Map<String, dynamic> json) =>
      _$CreateChatRequestFromJson(json);

  Map<String, dynamic> toJson() => _$CreateChatRequestToJson(this);

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is CreateChatRequest &&
          runtimeType == other.runtimeType &&
          title == other.title;

  @override
  int get hashCode => title.hashCode;

  @override
  String toString() => 'CreateChatRequest(title: $title)';
}

/// Response from creating a conversation
@JsonSerializable()
class CreateChatResponse {
  final String id;
  final String title;
  final DateTime createdAt;

  const CreateChatResponse({
    required this.id,
    required this.title,
    required this.createdAt,
  });

  factory CreateChatResponse.fromJson(Map<String, dynamic> json) =>
      _$CreateChatResponseFromJson(json);

  Map<String, dynamic> toJson() => _$CreateChatResponseToJson(this);

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is CreateChatResponse &&
          runtimeType == other.runtimeType &&
          id == other.id &&
          title == other.title &&
          createdAt == other.createdAt;

  @override
  int get hashCode => id.hashCode ^ title.hashCode ^ createdAt.hashCode;

  @override
  String toString() =>
      'CreateChatResponse(id: $id, title: $title, createdAt: $createdAt)';
}
