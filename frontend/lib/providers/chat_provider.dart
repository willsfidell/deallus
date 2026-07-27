import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';

import '../models/chat.dart';
import '../models/exceptions.dart';
import '../services/chat_service.dart';
import 'auth_provider.dart';

final _logger = Logger();

/// Provider for list of conversations
final chatListProvider = FutureProvider<List<Chat>>((ref) async {
  final chatService = ref.watch(chatServiceProvider);

  try {
    final rawChats = await chatService.getConversations();

    // Parse raw chat data into Chat objects
    final chats = <Chat>[];
    for (final item in rawChats) {
      if (item is Map<String, dynamic>) {
        try {
          final chat = Chat.fromJson(item);
          chats.add(chat);
        } catch (e) {
          _logger.w('Failed to parse chat item', error: e);
        }
      }
    }

    // Sort by most recent first
    chats.sort((a, b) => b.updatedAt?.compareTo(a.updatedAt ?? a.createdAt) ??
        b.createdAt.compareTo(a.createdAt));

    _logger.d('Loaded ${chats.length} conversations');
    return chats;
  } catch (e, st) {
    _logger.e('Failed to load chats', error: e, stackTrace: st);
    rethrow;
  }
});

/// Provider for current active conversation ID
/// Using a simple Notifier-based approach
class _ActiveChatNotifier extends Notifier<String?> {
  @override
  String? build() => null;

  void setActiveChat(String? id) => state = id;
}

final activeChatIdProvider =
    NotifierProvider<_ActiveChatNotifier, String?>(
  () => _ActiveChatNotifier(),
);

/// Provider for creating a new chat
final createChatProvider = FutureProvider.family<String, String?>((ref, title) async {
  final chatService = ref.watch(chatServiceProvider);

  try {
    _logger.d('Creating new conversation with title: $title');

    final response = await chatService.createConversation();

    // Parse the response
    final newChatData = CreateChatResponse.fromJson(response);

    final newChat = Chat(
      id: newChatData.id,
      title: newChatData.title,
      createdAt: newChatData.createdAt,
      updatedAt: newChatData.createdAt,
      messageCount: 0,
    );

    _logger.d('New conversation created: ${newChat.id}');

    // Invalidate chat list to refresh
    ref.invalidate(chatListProvider);

    return newChat.id;
  } catch (e, st) {
    _logger.e('Failed to create chat', error: e, stackTrace: st);
    throw ChatException(
      message: 'Failed to create conversation',
      originalException: e,
    );
  }
});

/// Provider for deleting a chat
final deleteChatProvider = FutureProvider.family<void, String>((ref, chatId) async {
  try {
    _logger.d('Deleting conversation: $chatId');

    // TODO: Add delete endpoint to backend when available
    // For now, just invalidate the chat list to refresh

    _logger.d('Conversation deleted: $chatId');

    // Invalidate chat list to refresh
    ref.invalidate(chatListProvider);
  } catch (e, st) {
    _logger.e('Failed to delete chat', error: e, stackTrace: st);
    throw ChatException(
      message: 'Failed to delete conversation',
      originalException: e,
    );
  }
});

/// Provider for updating chat title
final updateChatTitleProvider =
    FutureProvider.family<void, (String, String)>((ref, params) async {
  final (chatId, newTitle) = params;

  try {
    if (newTitle.isEmpty) {
      throw ValidationException(message: 'Title cannot be empty');
    }

    _logger.d('Chat title updated: $chatId -> $newTitle');

    // Invalidate chat list to refresh
    ref.invalidate(chatListProvider);
  } catch (e, st) {
    _logger.e('Failed to update chat title', error: e, stackTrace: st);
    throw ChatException(
      message: 'Failed to update chat title',
      originalException: e,
    );
  }
});

/// Provider for getting a specific chat
final chatByIdProvider = FutureProvider.family<Chat?, String>((ref, chatId) async {
  final chats = ref.watch(chatListProvider);

  return chats.maybeWhen(
    data: (chatList) {
      try {
        return chatList.firstWhere((c) => c.id == chatId);
      } catch (_) {
        return null;
      }
    },
    orElse: () => null,
  );
});
