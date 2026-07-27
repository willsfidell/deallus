import 'package:json_annotation/json_annotation.dart';

part 'api_response.g.dart';

/// Main response from /api/process endpoint
@JsonSerializable()
class ProcessResponse {
  final String conversationId;
  final String responseId;
  final String modelUsed;
  final String content;
  @JsonKey(name: 'routing_reason')
  final String routingReason;
  @JsonKey(name: 'continuity_applied')
  final bool continuityApplied;
  @JsonKey(name: 'context_used')
  final bool contextUsed;
  @JsonKey(name: 'total_tokens')
  final int totalTokens;
  @JsonKey(name: 'tools_executed')
  final List<ToolExecution> toolsExecuted;
  @JsonKey(name: 'timestamp')
  final DateTime timestamp;

  const ProcessResponse({
    required this.conversationId,
    required this.responseId,
    required this.modelUsed,
    required this.content,
    required this.routingReason,
    required this.continuityApplied,
    required this.contextUsed,
    required this.totalTokens,
    required this.toolsExecuted,
    required this.timestamp,
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
