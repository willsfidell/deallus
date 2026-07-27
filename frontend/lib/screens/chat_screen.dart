import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/chat_provider.dart';
import '../widgets/chat_panel/chat_panel_widget.dart';
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

    return ChatPanelWidget(conversationId: activeChat);
  }
}
