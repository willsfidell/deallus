import 'package:flutter/material.dart';

/// File attachment widget
class FileAttachmentWidget extends StatelessWidget {
  final String filename;
  final int sizeBytes;
  final String? url;
  final bool isUploading;
  final double uploadProgress;
  final VoidCallback? onDelete;
  final VoidCallback? onRetry;

  const FileAttachmentWidget({
    required this.filename,
    required this.sizeBytes,
    this.url,
    this.isUploading = false,
    this.uploadProgress = 0,
    this.onDelete,
    this.onRetry,
    Key? key,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  _getFileIcon(),
                  size: 32,
                  color: Colors.blue,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        filename,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.w500,
                            ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _formatFileSize(sizeBytes),
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                if (!isUploading)
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: onDelete,
                  ),
              ],
            ),
            if (isUploading) ...[
              const SizedBox(height: 8),
              LinearProgressIndicator(value: uploadProgress),
              const SizedBox(height: 4),
              Text(
                '${(uploadProgress * 100).toStringAsFixed(0)}%',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ],
        ),
      ),
    );
  }

  /// Get file icon based on type
  IconData _getFileIcon() {
    if (filename.endsWith('.pdf')) return Icons.picture_as_pdf;
    if (filename.endsWith('.doc') || filename.endsWith('.docx')) {
      return Icons.description;
    }
    if (filename.endsWith('.jpg') ||
        filename.endsWith('.jpeg') ||
        filename.endsWith('.png')) return Icons.image;
    return Icons.attach_file;
  }

  /// Format file size
  String _formatFileSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}
