import 'package:json_annotation/json_annotation.dart';

part 'api_response.g.dart';

/// Main response from /api/process endpoint
@JsonSerializable()
class ProcessResponse {
  @JsonKey(name: 'request_id')
  final String requestId;
  
  @JsonKey(name: 'conversation_id')
  final String? conversationId;
  
  @JsonKey(name: 'model_used')
  final String modelUsed;
  
  final String response;
  final String prompt;
  
  @JsonKey(name: 'execution_time_ms')
  final double executionTimeMs;
  
  @JsonKey(name: 'routing_reason')
  final String? routingReason;
  
  @JsonKey(name: 'continuity_applied')
  final bool continuityApplied;
  
  @JsonKey(name: 'context_used')
  final int contextUsed;
  
  @JsonKey(name: 'total_tokens')
  final int? totalTokens;
  
  @JsonKey(name: 'tools_executed', defaultValue: [])
  final List<ToolExecution> toolsExecuted;
  
  @JsonKey(name: 'tool_flags', defaultValue: {})
  final Map<String, dynamic> toolFlags;

  const ProcessResponse({
    required this.requestId,
    this.conversationId,
    required this.modelUsed,
    required this.response,
    required this.prompt,
    required this.executionTimeMs,
    this.routingReason,
    required this.continuityApplied,
    required this.contextUsed,
    this.totalTokens,
    this.toolsExecuted = const [],
    this.toolFlags = const {},
  });

  factory ProcessResponse.fromJson(Map<String, dynamic> json) =>
      _$ProcessResponseFromJson(json);

  Map<String, dynamic> toJson() => _$ProcessResponseToJson(this);
}

@JsonSerializable()
class ToolExecution {
  final String name;
  final String stage;
  final String action;
  final String description;

  const ToolExecution({
    required this.name,
    required this.stage,
    required this.action,
    required this.description,
  });

  factory ToolExecution.fromJson(Map<String, dynamic> json) =>
      _$ToolExecutionFromJson(json);

  Map<String, dynamic> toJson() => _$ToolExecutionToJson(this);
}

/// Health check response
@JsonSerializable()
class HealthResponse {
  final String status;
  final DateTime timestamp;
  final String? version;

  const HealthResponse({
    required this.status,
    required this.timestamp,
    this.version,
  });

  factory HealthResponse.fromJson(Map<String, dynamic> json) =>
      _$HealthResponseFromJson(json);

  Map<String, dynamic> toJson() => _$HealthResponseToJson(this);
}
