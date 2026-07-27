import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';

import '../models/message.dart';
import '../models/exceptions.dart';
import '../services/chat_service.dart';
import '../config/app_constants.dart';
import 'auth_provider.dart';

final _logger = Logger();

/// Simple provider for current conversation ID
class _CurrentConversationNotifier extends Notifier<String?> {
  @override
  String? build() => null;

  void setConversation(String? id) => state = id;
}

final currentConversationIdProvider =
    NotifierProvider<_CurrentConversationNotifier, String?>(
  () => _CurrentConversationNotifier(),
);

/// Provider for messages in current conversation - simple async provider
final conversationMessagesProvider =
    FutureProvider.family<List<Message>, String>(
  (ref, conversationId) async {
    final chatService = ref.watch(chatServiceProvider);
    return _fetchMessagesForConversation(chatService, conversationId);
  },
);

/// Helper function to fetch messages for conversation
Future<List<Message>> _fetchMessagesForConversation(
  ChatService chatService,
  String conversationId,
) async {
  try {
    final response = await chatService.getMessages(
      conversationId,
      page: 1,
      pageSize: AppConstants.messagePaginationSize,
    );

    _logger.d('Response: $response');

    // Parse the messages array from the conversation response
    final messagesList = response['messages'] as List<dynamic>? ?? [];
    
    if (messagesList.isEmpty) {
      _logger.d('No messages in conversation');
      return [];
    }

    final messages = <Message>[];
    for (final msg in messagesList) {
      try {
        if (msg is Map<String, dynamic>) {
          final message = Message.fromJson(msg);
          messages.add(message);
        }
      } catch (e) {
        _logger.w('Failed to parse message: $msg', error: e);
      }
    }

    messages.sort((a, b) => a.timestamp.compareTo(b.timestamp));

    _logger.d('Loaded ${messages.length} messages');
    return messages;
  } catch (e, st) {
    _logger.e('Failed to fetch messages', error: e, stackTrace: st);
    throw ConversationException(
      message: 'Failed to fetch messages: $e',
      originalException: e,
    );
  }
}

/// Simple alias for message list - using the conversation provider
final messagePaginationProvider = conversationMessagesProvider;
