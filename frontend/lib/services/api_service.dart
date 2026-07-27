import 'package:dio/dio.dart';
import 'package:logger/logger.dart';

import '../config/app_constants.dart';
import '../models/api_response.dart';
import '../models/exceptions.dart';

/// API endpoints configuration
abstract final class AppEndpoints {
  static const String health = '/api/health';
  static const String process = '/api/process';
  static const String conversations = '/api/conversations';
  static const String messages = '/api/conversations/{id}/messages';
}

/// HTTP client service using Dio
class ApiService {
  late final Dio _dio;
  final Logger _logger = Logger();
  String _apiUrl = AppConstants.defaultApiUrl;
  String? _apiKey;

  ApiService() {
    _initDio();
  }

  /// Initialize Dio with interceptors and configuration
  void _initDio() {
    _dio = Dio(
      BaseOptions(
        baseUrl: _apiUrl,
        connectTimeout: AppConstants.apiTimeout,
        receiveTimeout: AppConstants.apiTimeout,
        sendTimeout: AppConstants.apiTimeout,
        contentType: Headers.jsonContentType,
        responseType: ResponseType.json,
      ),
    );

    // Add logging interceptor
    _dio.interceptors.add(
      LoggingInterceptor(_logger),
    );

    // Add auth interceptor
    _dio.interceptors.add(
      AuthInterceptor(this),
    );
  }

  /// Update API configuration
  void updateConfig({
    required String apiUrl,
    required String apiKey,
  }) {
    _apiUrl = apiUrl;
    _apiKey = apiKey;
    _dio.options.baseUrl = apiUrl;
    _logger.i('API config updated: $apiUrl');
  }

  /// Get current API key
  String? get apiKey => _apiKey;

  /// Get current API URL
  String get apiUrl => _apiUrl;

  /// Check API health
  Future<HealthResponse> getHealth() async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        AppEndpoints.health,
      );
      return HealthResponse.fromJson(response.data!);
    } on DioException catch (e) {
      throw ApiException.from(e);
    }
  }

  /// Process a message (main chat endpoint)
  Future<ProcessResponse> processMessage({
    required String message,
    String? conversationId,
    String? model,
    bool forceModel = false,
  }) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        AppEndpoints.process,
        data: {
          'prompt': message,
          if (model != null) 'model': model,
          if (conversationId != null) 'conversation_id': conversationId,
          if (forceModel) 'force_model': forceModel,
        },
      );
      return ProcessResponse.fromJson(response.data!);
    } on DioException catch (e) {
      throw ApiException.from(e);
    }
  }

  /// Get list of conversations
  Future<List<dynamic>> getConversations() async {
    try {
      final response = await _dio.get<List<dynamic>>(
        AppEndpoints.conversations,
      );
      return response.data ?? [];
    } on DioException catch (e) {
      throw ApiException.from(e);
    }
  }

  /// Create a new conversation
  Future<Map<String, dynamic>> createConversation({
    String? title,
  }) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        AppEndpoints.conversations,
        data: {
          'title': title,
        },
      );
      return response.data ?? {};
    } on DioException catch (e) {
      throw ApiException.from(e);
    }
  }

  /// Get messages for a conversation (fetches the full conversation object)
  Future<Map<String, dynamic>> getMessages(
    String conversationId, {
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      // The messages are returned as part of the conversation object
      final endpoint = '${AppEndpoints.conversations}/$conversationId';
      
      final response = await _dio.get<Map<String, dynamic>>(
        endpoint,
        queryParameters: {
          'page': page,
          'page_size': pageSize,
        },
      );
      
      // Return the response which includes messages array
      return response.data ?? {};
    } on DioException catch (e) {
      throw ApiException.from(e);
    }
  }

  /// Upload file(s) with a message
  Future<ProcessResponse> uploadFilesWithMessage({
    required String message,
    required List<String> filePaths,
    String? conversationId,
  }) async {
    try {
      final formData = FormData();
      formData.fields.add(MapEntry('prompt', message));
      
      if (conversationId != null) {
        formData.fields.add(MapEntry('conversation_id', conversationId));
      }

      // Add files
      for (final filePath in filePaths) {
        formData.files.add(
          MapEntry(
            'files',
            await MultipartFile.fromFile(filePath),
          ),
        );
      }

      final response = await _dio.post<Map<String, dynamic>>(
        AppEndpoints.process,
        data: formData,
      );

      return ProcessResponse.fromJson(response.data!);
    } on DioException catch (e) {
      throw ApiException.from(e);
    }
  }

  /// Upload audio file for transcription
  Future<ProcessResponse> uploadAudioMessage({
    required String audioFilePath,
    required String? transcription,
    String? conversationId,
  }) async {
    try {
      final formData = FormData();
      
      if (conversationId != null) {
        formData.fields.add(MapEntry('conversation_id', conversationId));
      }

      if (transcription != null) {
        formData.fields.add(MapEntry('transcription', transcription));
      }

      formData.files.add(
        MapEntry(
          'audio',
          await MultipartFile.fromFile(audioFilePath),
        ),
      );

      final response = await _dio.post<Map<String, dynamic>>(
        AppEndpoints.process,
        data: formData,
      );

      return ProcessResponse.fromJson(response.data!);
    } on DioException catch (e) {
      throw ApiException.from(e);
    }
  }
}

/// Logging interceptor for Dio
class LoggingInterceptor extends Interceptor {
  final Logger _logger;

  LoggingInterceptor(this._logger);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    _logger.d(
      'REQUEST[${options.method}] => PATH: ${options.path}',
      error: options.data,
    );
    super.onRequest(options, handler);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    _logger.d(
      'RESPONSE[${response.statusCode}] => PATH: ${response.requestOptions.path}',
    );
    super.onResponse(response, handler);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    _logger.e(
      'ERROR[${err.response?.statusCode}] => PATH: ${err.requestOptions.path}',
      error: err,
      stackTrace: err.stackTrace,
    );
    super.onError(err, handler);
  }
}

/// Authentication interceptor to add API key to requests
class AuthInterceptor extends Interceptor {
  final ApiService _apiService;

  AuthInterceptor(this._apiService);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final apiKey = _apiService.apiKey;
    if (apiKey != null && apiKey.isNotEmpty) {
      options.headers[AppConstants.apiKeyHeader] = apiKey;
    }
    super.onRequest(options, handler);
  }
}
