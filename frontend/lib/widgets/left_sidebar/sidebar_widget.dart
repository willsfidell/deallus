import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';

import '../../providers/chat_provider.dart';
import '../../screens/settings_screen.dart';
import 'chat_list_item.dart';
import 'empty_chat_list.dart';
import 'new_chat_button.dart';
import 'settings_button.dart';

/// Main sidebar widget containing chat list and action buttons
class SidebarWidget extends ConsumerWidget {
  const SidebarWidget({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final chatsState = ref.watch(chatListProvider);
    final activeChat = ref.watch(activeChatIdProvider);
    final Logger logger = Logger();

    return Column(
      children: [
        // Header with New Chat Button
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: NewChatButton(
            onPressed: () async {
              try {
                // Use the createChatProvider instead of notifier
                await ref.read(createChatProvider(null).future);
              } catch (e) {
                logger.e('Failed to create new chat', error: e);
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Error: $e')),
                  );
                }
              }
            },
          ),
        ),

        // Chat List
        Expanded(
          child: chatsState.when(
            data: (chats) {
              if (chats.isEmpty) {
                return const EmptyChatList();
              }

              return ListView.builder(
                itemCount: chats.length,
                itemBuilder: (context, index) {
                  final chat = chats[index];
                  return ChatListItem(
                    chat: chat,
                    isActive: activeChat == chat.id,
                    onTap: () {
                      ref.read(activeChatIdProvider.notifier).setActiveChat(chat.id);
                    },
                    onDelete: () {
                      _showDeleteConfirmation(context, ref, chat.id);
                    },
                  );
                },
              );
            },
            loading: () => const Center(
              child: CircularProgressIndicator(),
            ),
            error: (error, st) => Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error, color: Colors.red),
                  const SizedBox(height: 8),
                  Text('Error: $error'),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      ref.refresh(chatListProvider);
                    },
                    child: const Text('Retry'),
                  ),
                ],
              ),
            ),
          ),
        ),

        // Bottom Settings Button
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: SettingsButton(
            onPressed: () {
              SettingsScreen.show(context);
            },
          ),
        ),
      ],
    );
  }

  /// Show delete confirmation dialog
  void _showDeleteConfirmation(
    BuildContext context,
    WidgetRef ref,
    String chatId,
  ) {
    showDialog(
      context: context,
      barrierDismissible: false, // Prevent accidental dismissal
      builder: (dialogContext) => AlertDialog(
        title: const Text('Delete Conversation?'),
        content: const Text(
          'This conversation will be permanently deleted. This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(dialogContext).pop(); // Use dialogContext instead of context
            },
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              try {
                // Use the deleteChatProvider instead of notifier
                await ref.read(deleteChatProvider(chatId).future);
                if (dialogContext.mounted) {
                  Navigator.of(dialogContext).pop(); // Use dialogContext
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Conversation deleted')),
                    );
                  }
                }
              } catch (e) {
                if (dialogContext.mounted) {
                  Navigator.of(dialogContext).pop(); // Use dialogContext
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Error deleting conversation: $e'),
                        backgroundColor: Colors.red,
                      ),
                    );
                  }
                }
              }
            },
            child: const Text('Delete', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }
}
