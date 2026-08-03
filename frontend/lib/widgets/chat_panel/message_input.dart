import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';

import '../../config/app_constants.dart';
import '../../providers/message_provider.dart';
import '../../providers/conversation_provider.dart';
import '../common/loading_indicator.dart';

/// Message input widget
class MessageInput extends ConsumerStatefulWidget {
  final String conversationId;

  const MessageInput({
    required this.conversationId,
    Key? key,
  }) : super(key: key);

  @override
  ConsumerState<MessageInput> createState() => _MessageInputState();
}

class _MessageInputState extends ConsumerState<MessageInput> {
  late TextEditingController _messageController;
  bool _isSending = false;
  final Logger _logger = Logger();
  List<String> _attachedFiles = [];

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

  /// Send message
  Future<void> _sendMessage() async {
    if (_messageController.text.isEmpty && _attachedFiles.isEmpty) {
      return;
    }

    try {
      setState(() {
        _isSending = true;
      });

      final params = SendMessageParams(
        conversationId: widget.conversationId,
        message: _messageController.text,
        filePaths: _attachedFiles.isNotEmpty ? _attachedFiles : null,
      );

      final response = await ref.read(
        sendMessageProvider(params).future,
      );

      // Refresh the message list to show the new message
      ref.refresh(conversationMessagesProvider(widget.conversationId));
      
      // Invalidate the sendMessageProvider to allow new messages to be sent
      ref.invalidate(sendMessageProvider);

      // Clear input
      _messageController.clear();
      _attachedFiles.clear();

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
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // File attachments preview
        if (_attachedFiles.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Wrap(
              spacing: 8,
              children: _attachedFiles
                  .map((file) => Chip(
                        label: Text(file.split('/').last),
                        onDeleted: () {
                          setState(() {
                            _attachedFiles.remove(file);
                          });
                        },
                      ))
                  .toList(),
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
                  decoration: InputDecoration(
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
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // File attachment button
                        Tooltip(
                          message: 'Attach files (max 4)',
                          child: IconButton(
                            icon: const Icon(Icons.attach_file),
                            onPressed: _isSending
                                ? null
                                : () {
                                    _logger.d('File picker not implemented yet');
                                  },
                          ),
                        ),

                        // Audio record button
                        Tooltip(
                          message: 'Record audio (max 2 min)',
                          child: IconButton(
                            icon: const Icon(Icons.mic),
                            onPressed: _isSending
                                ? null
                                : () {
                                    _logger.d('Audio recording not implemented yet');
                                  },
                          ),
                        ),
                      ],
                    ),

                    // Send button
                    Tooltip(
                      message: 'Send message',
                      child: FloatingActionButton(
                        onPressed: (_messageController.text.isEmpty &&
                                _attachedFiles.isEmpty) ||
                            _isSending
                            ? null
                            : _sendMessage,
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
