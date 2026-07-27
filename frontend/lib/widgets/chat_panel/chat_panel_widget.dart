import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/chat.dart';
import '../../providers/chat_provider.dart';
import '../common/loading_indicator.dart';
import 'message_list.dart';
import 'message_input.dart';

/// Main chat panel widget
class ChatPanelWidget extends ConsumerWidget {
  final String conversationId;

  const ChatPanelWidget({
    required this.conversationId,
    Key? key,
  }) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final chatsState = ref.watch(chatListProvider);

    return chatsState.when(
      data: (chats) {
        // Find current chat
        Chat? currentChat;
        try {
          currentChat = chats.firstWhere((c) => c.id == conversationId);
        } catch (_) {
          currentChat = null;
        }

        if (currentChat == null) {
          return const Center(
            child: Text('Conversation not found'),
          );
        }

        return Column(
          children: [
            // Chat Header
            _buildChatHeader(context, currentChat),

            // Message List
            Expanded(
              child: MessageList(conversationId: conversationId),
            ),

            // Message Input
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: MessageInput(conversationId: conversationId),
            ),
          ],
        );
      },
      loading: () => const LoadingIndicator(message: 'Loading conversations...'),
      error: (error, st) => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error, color: Colors.red, size: 48),
            const SizedBox(height: 16),
            Text('Error: $error'),
          ],
        ),
      ),
    );
  }

  /// Build chat header
  Widget _buildChatHeader(BuildContext context, Chat chat) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(color: Colors.grey.shade300),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  chat.title,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${chat.messageCount} messages',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey.shade600,
                      ),
                ),
              ],
            ),
          ),
          // Info button
          Tooltip(
            message: 'Conversation info',
            child: IconButton(
              icon: const Icon(Icons.info_outline),
              onPressed: () {
                // TODO: Show conversation info
              },
            ),
          ),
        ],
      ),
    );
  }
}
