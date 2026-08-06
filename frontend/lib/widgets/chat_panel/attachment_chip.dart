import 'package:flutter/material.dart';

import '../../models/attachment.dart';

typedef OnDelete = Function(String attachmentId);

class AttachmentChip extends StatelessWidget {
  const AttachmentChip({
    required this.attachment,
    required this.onDelete,
    super.key,
  });

  final Attachment attachment;
  final OnDelete onDelete;

  @override
  Widget build(BuildContext context) => Chip(
        avatar: _buildStatusIcon(),
        label: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              attachment.filename,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 12),
            ),
            Text(
              attachment.sizeDisplay,
              style: TextStyle(
                fontSize: 10,
                color: Colors.grey[600],
              ),
            ),
          ],
        ),
        deleteIcon: const Icon(Icons.close, size: 18),
        onDeleted: () => onDelete(attachment.id),
        backgroundColor: _getBackgroundColor(),
      );

  Widget _buildStatusIcon() {
    if (attachment.isUploading || attachment.isProcessing) {
      return const SizedBox(
        width: 16,
        height: 16,
        child: CircularProgressIndicator(strokeWidth: 2),
      );
    } else if (attachment.isCompleted) {
      return const Icon(Icons.check_circle, color: Colors.green, size: 18);
    } else if (attachment.isFailed) {
      return const Icon(Icons.error, color: Colors.red, size: 18);
    }
    return const Icon(Icons.description, size: 18);
  }

  Color? _getBackgroundColor() {
    if (attachment.isFailed) {
      return Colors.red[50];
    }
    if (attachment.isProcessing) {
      return Colors.yellow[50];
    }
    return Colors.green[50];
  }
}
