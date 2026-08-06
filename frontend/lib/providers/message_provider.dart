import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';

import '../models/api_response.dart';
import '../models/message.dart';
import '../models/exceptions.dart';
import '../services/chat_service.dart';
import '../services/cache_service.dart';
import '../config/app_constants.dart';
import 'auth_provider.dart';

final _logger = Logger();

/// Provider for CacheService singleton
final cacheServiceProvider = Provider<CacheService>((ref) {
  return CacheService();
});

/// Parameters for sending a message
class SendMessageParams {
  final String conversationId;
  final String message;
  final List<String>? filePaths;
  final String? audioFilePath;

  SendMessageParams({
    required this.conversationId,
    required this.message,
    this.filePaths,
    this.audioFilePath,
  });
}

/// Provider for sending a message
final sendMessageProvider =
    FutureProvider.autoDispose.family<Message, SendMessageParams>(
      (ref, params) async {
    final chatService = ref.watch(chatServiceProvider);
    return _sendMessage(chatService, params);
  },
);

/// Helper function to send a message
Future<Message> _sendMessage(
  ChatService chatService,
  SendMessageParams params,
) async {
  try {
    _logger.d('Sending message to conversation: ${params.conversationId}');

    ProcessResponse response;

    // Determine which send method to use
    if (params.audioFilePath != null) {
      response = await chatService.sendAudioMessage(
        audioFilePath: params.audioFilePath!,
        conversationId: params.conversationId,
      );
    } else if (params.filePaths != null && params.filePaths!.isNotEmpty) {
      // If filePaths contain attachment IDs (they are UUIDs), use sendMessageWithAttachments
      // Otherwise, use sendMessageWithFiles for file paths
      if (_isAttachmentIds(params.filePaths!)) {
        response = await chatService.sendMessageWithAttachments(
          message: params.message,
          attachmentIds: params.filePaths!,
          conversationId: params.conversationId,
        );
      } else {
        response = await chatService.sendMessageWithFiles(
          message: params.message,
          filePaths: params.filePaths!,
          conversationId: params.conversationId,
        );
      }
    } else {
      response = await chatService.sendMessage(
        message: params.message,
        conversationId: params.conversationId,
      );
    }

    // Convert response to Message object
    final message = Message(
      id: response.requestId,
      conversationId: response.conversationId ?? '',
      role: 'assistant',
      content: response.response,
      timestamp: DateTime.now(), // Use current time since backend doesn't return timestamp
    );

    _logger.d('Message sent successfully: ${message.id}');
    return message;
  } catch (e, st) {
    _logger.e('Failed to send message', error: e, stackTrace: st);
    throw MessageException(
      message: 'Failed to send message',
      originalException: e,
    );
  }
}

/// Helper to detect if strings are attachment IDs (UUIDs) vs file paths
bool _isAttachmentIds(List<String> items) {
  if (items.isEmpty) return false;
  // Check if first item looks like a UUID (no slashes or backslashes)
  return !items.first.contains('/') && !items.first.contains('\\');
}

/// Provider for deleting a message
final deleteMessageProvider = FutureProvider.family<void, (String, String)>(
  (ref, params) async {
    final (conversationId, messageId) = params;
    _logger.d('Deleting message: $messageId');
    // TODO: Implement message deletion when backend supports it
  },
);

/// Provider for editing a message
final editMessageProvider =
    FutureProvider.family<void, (String, String, String)>(
  (ref, params) async {
    final (conversationId, messageId, newContent) = params;
    _logger.d('Editing message: $messageId');
    // TODO: Implement message editing when backend supports it
  },
);

/// Provider for caching a message
final cacheMessageProvider = FutureProvider.family<void, Message>(
  (ref, message) async {
    final cacheService = ref.watch(cacheServiceProvider);
    try {
      _logger.d('Caching message: ${message.id}');
      // TODO: Implement when cache service is fully initialized
      _logger.d('Message cached: ${message.id}');
    } catch (e, st) {
      _logger.e('Failed to cache message', error: e, stackTrace: st);
      // Don't fail the operation if caching fails
    }
  },
);

/// Provider for caching multiple messages
final cacheMessagesProvider = FutureProvider.family<void, List<Message>>(
  (ref, messages) async {
    final cacheService = ref.watch(cacheServiceProvider);
    try {
      _logger.d('Caching ${messages.length} messages');
      // TODO: Implement when cache service is fully initialized
      _logger.d('Messages cached: ${messages.length}');
    } catch (e, st) {
      _logger.e('Failed to cache messages', error: e, stackTrace: st);
      // Don't fail the operation if caching fails
    }
  },
);

/// Provider for clearing conversation cache
final clearConversationCacheProvider =
    FutureProvider.family<void, String>((ref, conversationId) async {
  final cacheService = ref.watch(cacheServiceProvider);
  try {
    _logger.d('Clearing cache for conversation: $conversationId');
    await cacheService.clearConversationCache(conversationId);
    _logger.d('Cache cleared for conversation: $conversationId');
  } catch (e, st) {
    _logger.e('Failed to clear conversation cache', error: e, stackTrace: st);
    rethrow;
  }
});
