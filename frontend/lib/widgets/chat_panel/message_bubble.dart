import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../models/message.dart';
import 'markdown_renderer.dart';
import 'message_actions.dart';

/// Message bubble widget
class MessageBubble extends StatefulWidget {
  final Message message;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;
  final VoidCallback? onCopy;

  const MessageBubble({
    required this.message,
    this.onEdit,
    this.onDelete,
    this.onCopy,
    Key? key,
  }) : super(key: key);

  @override
  State<MessageBubble> createState() => _MessageBubbleState();
}

class _MessageBubbleState extends State<MessageBubble> {
  bool _showActions = false;

  @override
  Widget build(BuildContext context) {
    final isUser = widget.message.isUserMessage;

    return MouseRegion(
      onEnter: (_) {
        setState(() {
          _showActions = true;
        });
      },
      onExit: (_) {
        setState(() {
          _showActions = false;
        });
      },
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Row(
          mainAxisAlignment:
              isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
          children: [
            if (!isUser) ...[
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: Colors.blue.shade100,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Icon(Icons.smart_toy, size: 18),
              ),
              const SizedBox(width: 12),
            ],
            Flexible(
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Flexible(
                    child: Container(
                      constraints: BoxConstraints(
                        maxWidth: MediaQuery.of(context).size.width * 0.6,
                      ),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: isUser
                            ? Colors.blue.shade100
                            : Colors.grey.shade200,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          MarkdownRenderer(content: widget.message.content),
                          const SizedBox(height: 4),
                          Text(
                            _formatTime(widget.message.timestamp),
                            style: Theme.of(context)
                                .textTheme
                                .bodySmall
                                ?.copyWith(
                                  fontSize: 10,
                                  color: Colors.grey.shade600,
                                ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  if (_showActions && !isUser)
                    MessageActions(
                      onCopy: widget.onCopy,
                      onEdit: widget.onEdit,
                      onDelete: widget.onDelete,
                    ),
                ],
              ),
            ),
            if (isUser) ...[
              const SizedBox(width: 12),
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Icon(Icons.person, size: 18),
              ),
            ],
          ],
        ),
      ),
    );
  }

  /// Format time for display
  String _formatTime(DateTime time) {
    return DateFormat('HH:mm').format(time);
  }
}
