import 'package:logger/logger.dart';
import 'package:intl/intl.dart';
import 'dart:io';

import '../models/audio_recording.dart';
import '../models/exceptions.dart';

/// Service for exporting conversations
class ExportService {
  final Logger _logger = Logger();

  /// Export messages to markdown format
  String generateMarkdown({
    required String conversationId,
    required List<CachedMessage> messages,
    String? title,
  }) {
    try {
      final buffer = StringBuffer();
      
      // Header
      buffer.writeln('# ${title ?? conversationId}');
      buffer.writeln();
      buffer.writeln('**Exported:** ${DateFormat('yyyy-MM-dd HH:mm:ss').format(DateTime.now())}');
      buffer.writeln();
      buffer.writeln('---');
      buffer.writeln();

      // Sort messages chronologically
      final sortedMessages = [...messages]
        ..sort((a, b) => a.timestamp.compareTo(b.timestamp));

      // Add messages
      for (final message in sortedMessages) {
        buffer.writeln(
          '**${message.role == 'user' ? 'You' : 'Assistant'}** - ${DateFormat('HH:mm').format(message.timestamp)}',
        );
        buffer.writeln();
        
        // Message content
        buffer.writeln(message.content);
        buffer.writeln();

        // File attachments
        if (message.fileIds.isNotEmpty) {
          buffer.writeln('**Attachments:**');
          for (final fileId in message.fileIds) {
            buffer.writeln('- File: $fileId');
          }
          buffer.writeln();
        }

        // Audio attachment
        if (message.audioUrl != null) {
          buffer.writeln('**Audio:** ${message.audioUrl}');
          buffer.writeln();
        }

        buffer.writeln('---');
        buffer.writeln();
      }

      final markdown = buffer.toString();
      _logger.d('Generated markdown for $conversationId (${messages.length} messages)');
      return markdown;
    } catch (e) {
      _logger.e('Failed to generate markdown', error: e);
      throw FileException(
        message: 'Failed to generate markdown: $e',
        originalException: e,
      );
    }
  }

  /// Export as markdown file
  Future<String> exportAsMarkdownFile({
    required String conversationId,
    required List<CachedMessage> messages,
    required String outputPath,
    String? title,
  }) async {
    try {
      final markdown = generateMarkdown(
        conversationId: conversationId,
        messages: messages,
        title: title,
      );

      final file = File(outputPath);
      await file.writeAsString(markdown);

      _logger.d('Exported conversation to: $outputPath');
      return outputPath;
    } catch (e) {
      _logger.e('Failed to export markdown file', error: e);
      throw FileException(
        message: 'Failed to export file: $e',
        originalException: e,
      );
    }
  }

  /// Generate filename for export
  String generateExportFilename(String conversationId) {
    final timestamp = DateFormat('yyyy-MM-dd_HHmmss').format(DateTime.now());
    return '${conversationId}_$timestamp.md';
  }

  /// Export to CSV (alternative format)
  String generateCsv({
    required String conversationId,
    required List<CachedMessage> messages,
  }) {
    try {
      final buffer = StringBuffer();
      
      // CSV header
      buffer.writeln('timestamp,role,content,hasFiles,hasAudio');

      // Sort messages chronologically
      final sortedMessages = [...messages]
        ..sort((a, b) => a.timestamp.compareTo(b.timestamp));

      // Add messages
      for (final message in sortedMessages) {
        final timestamp = DateFormat('yyyy-MM-dd HH:mm:ss').format(message.timestamp);
        final content = '\"${message.content.replaceAll('"', '""')}\"';
        final hasFiles = message.fileIds.isNotEmpty ? 'true' : 'false';
        final hasAudio = message.audioUrl != null ? 'true' : 'false';

        buffer.writeln('$timestamp,${message.role},$content,$hasFiles,$hasAudio');
      }

      _logger.d('Generated CSV for $conversationId (${messages.length} messages)');
      return buffer.toString();
    } catch (e) {
      _logger.e('Failed to generate CSV', error: e);
      throw FileException(
        message: 'Failed to generate CSV: $e',
        originalException: e,
      );
    }
  }
}
