// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'api_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ProcessResponse _$ProcessResponseFromJson(Map<String, dynamic> json) =>
    ProcessResponse(
      requestId: json['request_id'] as String,
      conversationId: json['conversation_id'] as String?,
      modelUsed: json['model_used'] as String,
      response: json['response'] as String,
      prompt: json['prompt'] as String,
      executionTimeMs: (json['execution_time_ms'] as num).toDouble(),
      routingReason: json['routing_reason'] as String?,
      continuityApplied: json['continuity_applied'] as bool,
      contextUsed: (json['context_used'] as num).toInt(),
      totalTokens: (json['total_tokens'] as num?)?.toInt(),
      toolsExecuted: (json['tools_executed'] as List<dynamic>?)
              ?.map((e) => ToolExecution.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      toolFlags: json['tool_flags'] as Map<String, dynamic>? ?? {},
    );

Map<String, dynamic> _$ProcessResponseToJson(ProcessResponse instance) =>
    <String, dynamic>{
      'request_id': instance.requestId,
      'conversation_id': instance.conversationId,
      'model_used': instance.modelUsed,
      'response': instance.response,
      'prompt': instance.prompt,
      'execution_time_ms': instance.executionTimeMs,
      'routing_reason': instance.routingReason,
      'continuity_applied': instance.continuityApplied,
      'context_used': instance.contextUsed,
      'total_tokens': instance.totalTokens,
      'tools_executed': instance.toolsExecuted,
      'tool_flags': instance.toolFlags,
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
