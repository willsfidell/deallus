import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/chat_provider.dart';
import '../widgets/common/empty_state.dart';

/// Chat screen - right panel
class ChatScreen extends ConsumerWidget {
  const ChatScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final activeChat = ref.watch(activeChatIdProvider);

    if (activeChat == null) {
      return const Center(
        child: EmptyState(
          icon: Icons.inbox,
          title: 'Select a conversation',
          message: 'Choose a conversation from the left panel to get started',
        ),
      );
    }

    // TODO: Enable ChatPanelWidget once messagePaginationProvider is fixed
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.chat, size: 64, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text(
            'Chat for: $activeChat',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Text(
            'Chat panel UI coming soon',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Colors.grey[600],
            ),
          ),
        ],
      ),
    );
  }
}
