import 'dart:io';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';

import '../models/attachment.dart';
import '../services/attachment_service.dart';
import 'auth_provider.dart';

final _logger = Logger();

class AttachmentState {
  final List<Attachment> attachments;
  final bool isUploading;
  final String? error;

  AttachmentState({
    required this.attachments,
    required this.isUploading,
    this.error,
  });

  factory AttachmentState.initial() => AttachmentState(
    attachments: [],
    isUploading: false,
  );

  AttachmentState copyWith({
    List<Attachment>? attachments,
    bool? isUploading,
    String? error,
  }) =>
      AttachmentState(
        attachments: attachments ?? this.attachments,
        isUploading: isUploading ?? this.isUploading,
        error: error,
      );

  bool get canSend =>
      attachments.every((a) => a.isCompleted) &&
      !isUploading &&
      error == null;
}

class AttachmentNotifier extends Notifier<AttachmentState> {
  late final AttachmentService _service;

  @override
  AttachmentState build() {
    _service = ref.watch(attachmentServiceProvider);
    return AttachmentState.initial();
  }

  Future<void> uploadFile(File file) async {
    state = state.copyWith(isUploading: true, error: null);

    try {
      final attachment = await _service.uploadFile(file);

      state = state.copyWith(
        attachments: [...state.attachments, attachment],
        isUploading: false,
      );

      // If processing, start polling
      if (attachment.isProcessing) {
        _pollAttachment(attachment.id);
      }
    } catch (e) {
      _logger.e('Upload failed: $e');
      state = state.copyWith(
        isUploading: false,
        error: 'Upload failed: ${e.toString()}',
      );
    }
  }

  void _pollAttachment(String attachmentId) {
    _service.pollStatus(attachmentId).listen(
      (attachment) =>
          state = state.copyWith(
            attachments: state.attachments.map((a) =>
                a.id == attachmentId ? attachment : a
            ).toList(),
          ),
      onError: (e) => _logger.e('Polling failed: $e'),
    );
  }

  Future<void> removeAttachment(String attachmentId) async {
    try {
      await _service.deleteAttachment(attachmentId);

      state = state.copyWith(
        attachments: state.attachments
            .where((a) => a.id != attachmentId)
            .toList(),
      );
    } catch (e) {
      _logger.e('Delete failed: $e');
    }
  }

  void clearAttachments() {
    state = AttachmentState.initial();
  }
}

final attachmentServiceProvider = Provider((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return AttachmentService(apiService);
});

final attachmentProvider =
    NotifierProvider<AttachmentNotifier, AttachmentState>(
  AttachmentNotifier.new,
);


