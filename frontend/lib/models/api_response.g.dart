// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'api_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ProcessResponse _$ProcessResponseFromJson(Map<String, dynamic> json) =>
    ProcessResponse(
      conversationId: json['conversationId'] as String,
      responseId: json['responseId'] as String,
      modelUsed: json['modelUsed'] as String,
      content: json['content'] as String,
      routingReason: json['routing_reason'] as String,
      continuityApplied: json['continuity_applied'] as bool,
      contextUsed: json['context_used'] as bool,
      totalTokens: (json['total_tokens'] as num).toInt(),
      toolsExecuted: (json['tools_executed'] as List<dynamic>)
          .map((e) => ToolExecution.fromJson(e as Map<String, dynamic>))
          .toList(),
      timestamp: DateTime.parse(json['timestamp'] as String),
    );

Map<String, dynamic> _$ProcessResponseToJson(ProcessResponse instance) =>
    <String, dynamic>{
      'conversationId': instance.conversationId,
      'responseId': instance.responseId,
      'modelUsed': instance.modelUsed,
      'content': instance.content,
      'routing_reason': instance.routingReason,
      'continuity_applied': instance.continuityApplied,
      'context_used': instance.contextUsed,
      'total_tokens': instance.totalTokens,
      'tools_executed': instance.toolsExecuted,
      'timestamp': instance.timestamp.toIso8601String(),
    };

ToolExecution _$ToolExecutionFromJson(Map<String, dynamic> json) =>
    ToolExecution(
      name: json['name'] as String,
      stage: json['stage'] as String,
      action: json['action'] as String,
      description: json['description'] as String,
    );

Map<String, dynamic> _$ToolExecutionToJson(ToolExecution instance) =>
    <String, dynamic>{
      'name': instance.name,
      'stage': instance.stage,
      'action': instance.action,
      'description': instance.description,
    };

HealthResponse _$HealthResponseFromJson(Map<String, dynamic> json) =>
    HealthResponse(
      status: json['status'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
      version: json['version'] as String?,
    );

Map<String, dynamic> _$HealthResponseToJson(HealthResponse instance) =>
    <String, dynamic>{
      'status': instance.status,
      'timestamp': instance.timestamp.toIso8601String(),
      'version': instance.version,
    };
