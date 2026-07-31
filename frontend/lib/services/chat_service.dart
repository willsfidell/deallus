import 'package:logger/logger.dart';

import '../models/api_response.dart';
import '../models/exceptions.dart';
import 'api_service.dart';

/// High-level service for chat operations
class ChatService {
  final ApiService _apiService;
  final Logger _logger = Logger();

  ChatService(this._apiService);

  /// Send a text message
  Future<ProcessResponse> sendMessage({
    required String message,
    String? conversationId,
  }) async {
    try {
      if (message.trim().isEmpty) {
        throw ValidationException(
          message: 'Message cannot be empty',
        );
      }

      return await _apiService.processMessage(
        message: message,
        conversationId: conversationId,
      );
    } catch (e) {
      _logger.e('Failed to send message', error: e);
      rethrow;
    }
  }

  /// Send message with file attachments
  Future<ProcessResponse> sendMessageWithFiles({
    required String message,
    required List<String> filePaths,
    String? conversationId,
  }) async {
    try {
      if (message.trim().isEmpty && filePaths.isEmpty) {
        throw ValidationException(
          message: 'Message and files cannot both be empty',
        );
      }

      if (filePaths.length > 4) {
        throw ValidationException(
          message: 'Maximum 4 files per message',
        );
      }

      return await _apiService.uploadFilesWithMessage(
        message: message,
        filePaths: filePaths,
        conversationId: conversationId,
      );
    } catch (e) {
      _logger.e('Failed to send message with files', error: e);
      rethrow;
    }
  }

  /// Send audio message
  Future<ProcessResponse> sendAudioMessage({
    required String audioFilePath,
    String? transcription,
    String? conversationId,
  }) async {
    try {
      return await _apiService.uploadAudioMessage(
        audioFilePath: audioFilePath,
        transcription: transcription,
        conversationId: conversationId,
      );
    } catch (e) {
      _logger.e('Failed to send audio message', error: e);
      rethrow;
    }
  }

  /// Get conversations list
  Future<List<dynamic>> getConversations() async {
    try {
      return await _apiService.getConversations();
    } catch (e) {
      _logger.e('Failed to get conversations', error: e);
      rethrow;
    }
  }

  /// Create new conversation
  Future<Map<String, dynamic>> createConversation({
    String? title,
  }) async {
    try {
      return await _apiService.createConversation(title: title);
    } catch (e) {
      _logger.e('Failed to create conversation', error: e);
      rethrow;
    }
  }

  /// Get messages for conversation with pagination
  Future<Map<String, dynamic>> getMessages(
    String conversationId, {
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      return await _apiService.getMessages(
        conversationId,
        page: page,
        pageSize: pageSize,
      );
    } catch (e) {
      _logger.e('Failed to get messages', error: e);
      rethrow;
    }
  }

  /// Delete a conversation
  Future<void> deleteConversation(String conversationId) async {
    try {
      await _apiService.deleteConversation(conversationId);
    } catch (e) {
      _logger.e('Failed to delete conversation', error: e);
      rethrow;
    }
  }

  /// Verify API is reachable
  Future<bool> verifyApiHealth() async {
    try {
      await _apiService.getHealth();
      return true;
    } catch (e) {
      _logger.w('API health check failed', error: e);
      return false;
    }
  }
}
