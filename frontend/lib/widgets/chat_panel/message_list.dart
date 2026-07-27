import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';

import '../../providers/conversation_provider.dart';
import '../common/loading_indicator.dart';
import 'message_bubble.dart';

/// Message list widget with pagination
class MessageList extends ConsumerStatefulWidget {
  final String conversationId;

  const MessageList({
    required this.conversationId,
    Key? key,
  }) : super(key: key);

  @override
  ConsumerState<MessageList> createState() => _MessageListState();
}

class _MessageListState extends ConsumerState<MessageList> {
  final Logger _logger = Logger();
  late ScrollController _scrollController;

  @override
  void initState() {
    super.initState();
    _scrollController = ScrollController();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _scrollController.dispose();
    super.dispose();
  }

  /// Handle scroll for pagination
  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent * 0.8) {
      // Load more when user scrolls to 80% of the bottom
      final notifier = ref.read(
        messagePaginationProvider(widget.conversationId).notifier,
      );
      notifier.loadMoreMessages();
    }
  }

  @override
  Widget build(BuildContext context) {
    final paginationState = ref.watch(
      messagePaginationProvider(widget.conversationId),
    );

    return paginationState.maybeWhen(
      data: (state) {
        if (state.messages.isEmpty) {
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

        return Stack(
          children: [
            ListView.builder(
              controller: _scrollController,
              reverse: true,
              itemCount: state.messages.length + (state.hasMoreMessages ? 1 : 0),
              itemBuilder: (context, index) {
                // Loading indicator at top when loading more
                if (index == state.messages.length) {
                  return Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Center(
                      child: state.isLoading
                          ? const SizedBox(
                              height: 30,
                              width: 30,
                              child: CircularProgressIndicator(),
                            )
                          : const SizedBox.shrink(),
                    ),
                  );
                }

                // Messages in reverse order (newest at bottom)
                final messageIndex = state.messages.length - 1 - index;
                final message = state.messages[messageIndex];

                return MessageBubble(
                  message: message,
                  onCopy: () {
                    _copyMessage(message.content);
                  },
                  onEdit: () {
                    _logger.d('Edit not implemented yet');
                  },
                  onDelete: () {
                    _logger.d('Delete not implemented yet');
                  },
                );
              },
            ),
            // Error message
            if (state.error != null)
              Positioned(
                bottom: 16,
                left: 16,
                right: 16,
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.red.shade100,
                    border: Border.all(color: Colors.red.shade300),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error, color: Colors.red),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          state.error!,
                          style: const TextStyle(color: Colors.red),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, size: 18),
                        onPressed: () {
                          ref
                              .read(messagePaginationProvider(widget.conversationId).notifier)
                              .refresh();
                        },
                      ),
                    ],
                  ),
                ),
              ),
          ],
        );
      },
      loading: () => const LoadingIndicator(message: 'Loading messages...'),
      error: (error, st) {
        _logger.e('Message list error', error: error, stackTrace: st);
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error, color: Colors.red, size: 48),
              const SizedBox(height: 16),
              Text('Error loading messages: $error'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () {
                  ref.refresh(messagePaginationProvider(widget.conversationId));
                },
                child: const Text('Retry'),
              ),
            ],
          ),
        );
      },
      orElse: () => const LoadingIndicator(),
    );
  }

  /// Copy message content
  void _copyMessage(String content) {
    // TODO: Implement clipboard copy
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Message copied to clipboard')),
    );
  }
}
