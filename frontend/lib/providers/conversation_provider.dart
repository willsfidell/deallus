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

/// Provider for messages in current conversation
final conversationMessagesProvider =
    FutureProvider.family<List<Message>, String>(
  (ref, conversationId) async {
    final chatService = ref.watch(chatServiceProvider);
    return _fetchMessagesForConversation(chatService, conversationId);
  },
);

/// Simple provider for pagination state
final messagePaginationProvider =
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

    final messagesResponse = MessagesResponse.fromJson(response);
    final messages = messagesResponse.messages;

    messages.sort((a, b) => a.timestamp.compareTo(b.timestamp));

    return messages;
  } catch (e) {
    throw ConversationException(
      message: 'Failed to fetch messages',
      originalException: e,
    );
  }
}
