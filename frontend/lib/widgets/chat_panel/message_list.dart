import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';

import '../../providers/conversation_provider.dart';
import '../common/loading_indicator.dart';
import 'message_bubble.dart';

/// Message list widget
class MessageList extends ConsumerWidget {
  final String conversationId;

  const MessageList({
    required this.conversationId,
    Key? key,
  }) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final Logger logger = Logger();
    final messagesState = ref.watch(
      conversationMessagesProvider(conversationId),
    );

    return messagesState.when(
      data: (messages) {
        if (messages.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.chat_bubble_outline,
                    size: 64, color: Colors.grey.shade400),
                const SizedBox(height: 16),
                Text(
                  'No messages yet',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ],
            ),
          );
        }

        return ListView.builder(
          reverse: true,
          itemCount: messages.length,
          itemBuilder: (context, index) {
            final message = messages[messages.length - 1 - index];
            return MessageBubble(message: message);
          },
        );
      },
      loading: () => const Center(child: LoadingIndicator()),
      error: (error, st) {
        logger.e('Error loading messages', error: error, stackTrace: st);
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error_outline, size: 64, color: Colors.red.shade400),
              const SizedBox(height: 16),
              Text(
                'Failed to load messages',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Text(
                error.toString(),
                style: Theme.of(context).textTheme.bodySmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () {
                  ref.refresh(conversationMessagesProvider(conversationId));
                },
                child: const Text('Retry'),
              ),
            ],
          ),
        );
      },
    );
  }
}
