import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';

import '../../providers/attachment_provider.dart';
import '../../providers/conversation_provider.dart';
import '../../providers/message_provider.dart';
import 'attachment_chip.dart';
import 'file_picker_button.dart';

/// Message input widget
class MessageInput extends ConsumerStatefulWidget {
  final String conversationId;

  const MessageInput({
    required this.conversationId,
    super.key,
  });

  @override
  ConsumerState<MessageInput> createState() => _MessageInputState();
}

class _MessageInputState extends ConsumerState<MessageInput> {
  late TextEditingController _messageController;
  bool _isSending = false;
  final Logger _logger = Logger();

  @override
  void initState() {
    super.initState();
    _messageController = TextEditingController();
    // Listen to text changes to trigger rebuild
    _messageController.addListener(() {
      setState(() {
        // This will trigger a rebuild when text changes
      });
    });
  }

  @override
  void dispose() {
    _messageController.dispose();
    super.dispose();
  }

  /// Send message with attachment IDs
  Future<void> _sendMessage(WidgetRef ref) async {
    if (_messageController.text.isEmpty) {
      return;
    }

    try {
      setState(() {
        _isSending = true;
      });

      final attachmentState = ref.read(attachmentProvider);
      final attachmentIds =
          attachmentState.attachments.map((a) => a.id).toList();

      final params = SendMessageParams(
        conversationId: widget.conversationId,
        message: _messageController.text,
        filePaths: attachmentIds.isNotEmpty ? attachmentIds : null,
      );

      await ref.read(
        sendMessageProvider(params).future,
      );

      // Refresh the message list to show the new message
      // ignore: unused_result
      ref.refresh(conversationMessagesProvider(widget.conversationId));

      // Invalidate the sendMessageProvider to allow new messages to be sent
      ref
        ..invalidate(sendMessageProvider)
        ..read(attachmentProvider.notifier).clearAttachments();

      // Clear input
      _messageController.clear();

      _logger.d('Message sent successfully');

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Message sent'),
            duration: Duration(seconds: 1),
          ),
        );
      }
    } catch (e) {
      _logger.e('Failed to send message', error: e);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isSending = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final attachmentState = ref.watch(attachmentProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Show attachment chips if any
        if (attachmentState.attachments.isNotEmpty)
          Padding(
            padding: const EdgeInsets.all(8),
            child: Wrap(
              spacing: 8,
              runSpacing: 4,
              children: attachmentState.attachments.map((att) =>
                  AttachmentChip(
                    attachment: att,
                    onDelete: (id) => ref
                        .read(attachmentProvider.notifier)
                        .removeAttachment(id),
                  )).toList(),
            ),
          ),

        // Show error if any
        if (attachmentState.error != null)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            child: Text(
              attachmentState.error!,
              style: const TextStyle(color: Colors.red, fontSize: 12),
            ),
          ),

        // Input area
        Container(
          decoration: BoxDecoration(
            border: Border.all(color: Colors.grey.shade300),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            children: [
              // Message input
              Padding(
                padding: const EdgeInsets.all(12),
                child: TextField(
                  controller: _messageController,
                  maxLines: 4,
                  minLines: 1,
                  decoration: const InputDecoration(
                    hintText: 'Type a message...',
                    border: InputBorder.none,
                    contentPadding: EdgeInsets.zero,
                    isDense: true,
                  ),
                  enabled: !_isSending,
                ),
              ),

              // Action buttons
              Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // File attachment button
                        FilePickerButton(
                          onFilesSelected: (filePaths) {
                            for (final path in filePaths) {
                              final file = File(path);
                              ref
                                  .read(attachmentProvider.notifier)
                                  .uploadFile(file);
                            }
                          },
                        ),

                        // Audio record button
                        Tooltip(
                          message: 'Record audio (max 2 min)',
                          child: IconButton(
                            icon: const Icon(Icons.mic),
                            onPressed: _isSending
                                ? null
                                : () => _logger.d(
                                    'Audio recording not implemented yet'),
                          ),
                        ),
                      ],
                    ),

                    // Send button
                    Tooltip(
                      message: 'Send message',
                      child: FloatingActionButton(
                        onPressed:
                            (_messageController.text.isEmpty) || _isSending
                                ? null
                                : () => _sendMessage(ref),
                        mini: true,
                        child: _isSending
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                            : const Icon(Icons.send),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
