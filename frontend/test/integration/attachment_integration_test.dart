import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:deallus_frontend/models/attachment.dart';
import 'package:deallus_frontend/providers/attachment_provider.dart';

void main() {
  group('Attachment Feature - End-to-End Integration Tests', () {
    late ProviderContainer container;

    setUp(() {
      container = ProviderContainer();
    });

    tearDown(() {
      container.dispose();
    });

    // ============================================================================
    // ATTACHMENT STATE TESTS
    // ============================================================================

    group('Attachment State Management', () {
      test('initial state has empty attachments', () {
        final state = container.read(attachmentProvider);
        expect(state.attachments, isEmpty);
        expect(state.isUploading, isFalse);
        expect(state.error, isNull);
      });

      test('canSend is true when state is empty and no errors', () {
        final state = container.read(attachmentProvider);
        expect(state.canSend, isTrue);
      });

      test('attachment state copyWith works correctly', () {
        final attachment = const Attachment(
          id: 'att-1',
          filename: 'test.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 1024,
          status: 'completed',
        );

        final state = AttachmentState(
          attachments: [attachment],
          isUploading: false,
        );

        final updated = state.copyWith(
          attachments: [...state.attachments],
          isUploading: true,
        );

        expect(updated.isUploading, isTrue);
        expect(updated.attachments, hasLength(1));
      });
    });

    // ============================================================================
    // ATTACHMENT MODEL TESTS
    // ============================================================================

    group('Attachment Model', () {
      test('displays file size in bytes', () {
        const attachment = Attachment(
          id: 'att-1',
          filename: 'test.txt',
          mimeType: 'text/plain',
          sizeBytes: 512,
          status: 'completed',
        );

        expect(attachment.sizeDisplay, equals('512 B'));
      });

      test('displays file size in KB', () {
        const attachment = Attachment(
          id: 'att-1',
          filename: 'test.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 2048,
          status: 'completed',
        );

        expect(attachment.sizeDisplay, equals('2.0 KB'));
      });

      test('displays file size in MB', () {
        const attachment = Attachment(
          id: 'att-1',
          filename: 'large.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 5242880,
          status: 'completed',
        );

        expect(attachment.sizeDisplay, equals('5.0 MB'));
      });

      test('isCompleted returns true for completed status', () {
        const attachment = Attachment(
          id: 'att-1',
          filename: 'test.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 1024,
          status: 'completed',
        );

        expect(attachment.isCompleted, isTrue);
        expect(attachment.isUploading, isFalse);
        expect(attachment.isProcessing, isFalse);
        expect(attachment.isFailed, isFalse);
      });

      test('isUploading returns true for uploading status', () {
        const attachment = Attachment(
          id: 'att-1',
          filename: 'test.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 1024,
          status: 'uploading',
        );

        expect(attachment.isUploading, isTrue);
        expect(attachment.isCompleted, isFalse);
        expect(attachment.isProcessing, isFalse);
        expect(attachment.isFailed, isFalse);
      });

      test('isProcessing returns true for processing status', () {
        const attachment = Attachment(
          id: 'att-1',
          filename: 'test.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 1024,
          status: 'processing',
        );

        expect(attachment.isProcessing, isTrue);
        expect(attachment.isCompleted, isFalse);
        expect(attachment.isUploading, isFalse);
        expect(attachment.isFailed, isFalse);
      });

      test('isFailed returns true for failed status', () {
        const attachment = Attachment(
          id: 'att-1',
          filename: 'test.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 1024,
          status: 'failed',
          error: 'Upload failed',
        );

        expect(attachment.isFailed, isTrue);
        expect(attachment.isCompleted, isFalse);
        expect(attachment.isUploading, isFalse);
        expect(attachment.isProcessing, isFalse);
      });

      test('copyWith creates new attachment with updated fields', () {
        const original = Attachment(
          id: 'att-1',
          filename: 'test.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 1024,
          status: 'uploading',
        );

        final updated = original.copyWith(
          status: 'processing',
          extractedTextPreview: 'Extracted text',
        );

        expect(updated.id, equals(original.id));
        expect(updated.filename, equals(original.filename));
        expect(updated.status, equals('processing'));
        expect(updated.extractedTextPreview, equals('Extracted text'));
      });

      test('attachment serialization works', () {
        const attachment = Attachment(
          id: 'att-1',
          filename: 'document.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 1024,
          status: 'completed',
          pageCount: 5,
          wordCount: 250,
        );

        final json = attachment.toJson();
        expect(json['id'], equals('att-1'));
        expect(json['filename'], equals('document.pdf'));
        expect(json['mime_type'], equals('application/pdf'));
        expect(json['page_count'], equals(5));

        // Deserialize
        final restored = Attachment.fromJson(json);
        expect(restored.id, equals(attachment.id));
        expect(restored.filename, equals(attachment.filename));
        expect(restored.pageCount, equals(attachment.pageCount));
      });
    });

    // ============================================================================
    // NOTIFIER TESTS - Upload, Delete, Clear operations
    // ============================================================================

    group('Attachment Notifier - Operations', () {
      test('clearAttachments resets state to initial', () {
        // Setup: Add an attachment manually to state
        final notifier = container.read(attachmentProvider.notifier);
        var state = container.read(attachmentProvider);
        
        // Simulate an error state
        final initialState = state.copyWith(
          error: 'Some error',
          isUploading: true,
        );

        // Clear
        notifier.clearAttachments();

        state = container.read(attachmentProvider);
        expect(state.attachments, isEmpty);
        expect(state.isUploading, isFalse);
        expect(state.error, isNull);
      });

      test('removeAttachment can be called on empty list', () async {
        final notifier = container.read(attachmentProvider.notifier);
        
        // Should not throw
        await notifier.removeAttachment('att-1');
        
        final state = container.read(attachmentProvider);
        expect(state.attachments, isEmpty);
      });
    });

    // ============================================================================
    // UPLOAD FLOW SCENARIOS
    // ============================================================================

    group('Upload Flow Scenarios', () {
      test('multiple attachments can be added to state', () {
        const att1 = Attachment(
          id: 'att-1',
          filename: 'file1.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 1024,
          status: 'completed',
        );

        const att2 = Attachment(
          id: 'att-2',
          filename: 'file2.docx',
          mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          sizeBytes: 2048,
          status: 'completed',
        );

        const att3 = Attachment(
          id: 'att-3',
          filename: 'file3.txt',
          mimeType: 'text/plain',
          sizeBytes: 512,
          status: 'completed',
        );

        var state = AttachmentState(
          attachments: [att1],
          isUploading: false,
        );

        // Add second
        state = state.copyWith(
          attachments: [...state.attachments, att2],
        );

        expect(state.attachments, hasLength(2));
        expect(state.attachments[0].id, equals('att-1'));
        expect(state.attachments[1].id, equals('att-2'));

        // Add third
        state = state.copyWith(
          attachments: [...state.attachments, att3],
        );

        expect(state.attachments, hasLength(3));
        expect(state.attachments.map((a) => a.id).toList(),
            equals(['att-1', 'att-2', 'att-3']));
      });

      test('attachment list maintains upload order', () {
        final attachments = [
          const Attachment(
            id: 'att-1',
            filename: 'first.pdf',
            mimeType: 'application/pdf',
            sizeBytes: 1024,
            status: 'completed',
          ),
          const Attachment(
            id: 'att-2',
            filename: 'second.pdf',
            mimeType: 'application/pdf',
            sizeBytes: 1024,
            status: 'completed',
          ),
          const Attachment(
            id: 'att-3',
            filename: 'third.pdf',
            mimeType: 'application/pdf',
            sizeBytes: 1024,
            status: 'completed',
          ),
        ];

        final state = AttachmentState(
          attachments: attachments,
          isUploading: false,
        );

        expect(state.attachments[0].filename, equals('first.pdf'));
        expect(state.attachments[1].filename, equals('second.pdf'));
        expect(state.attachments[2].filename, equals('third.pdf'));
      });
    });

    // ============================================================================
    // SEND MESSAGE STATE VALIDATION TESTS
    // ============================================================================

    group('Send Message State Validation', () {
      test('canSend is true when all attachments completed', () {
        final state = AttachmentState(
          attachments: [
            const Attachment(
              id: 'att-1',
              filename: 'test.pdf',
              mimeType: 'application/pdf',
              sizeBytes: 1024,
              status: 'completed',
            ),
          ],
          isUploading: false,
          error: null,
        );

        expect(state.canSend, isTrue);
      });

      test('canSend is false when attachment is uploading', () {
        final state = AttachmentState(
          attachments: [
            const Attachment(
              id: 'att-1',
              filename: 'test.pdf',
              mimeType: 'application/pdf',
              sizeBytes: 1024,
              status: 'uploading',
            ),
          ],
          isUploading: true,
          error: null,
        );

        expect(state.canSend, isFalse);
      });

      test('canSend is false when attachment is processing', () {
        final state = AttachmentState(
          attachments: [
            const Attachment(
              id: 'att-1',
              filename: 'test.pdf',
              mimeType: 'application/pdf',
              sizeBytes: 1024,
              status: 'processing',
            ),
          ],
          isUploading: false,
          error: null,
        );

        expect(state.canSend, isFalse);
      });

      test('canSend is false when there is an error', () {
        final state = AttachmentState(
          attachments: [
            const Attachment(
              id: 'att-1',
              filename: 'test.pdf',
              mimeType: 'application/pdf',
              sizeBytes: 1024,
              status: 'completed',
            ),
          ],
          isUploading: false,
          error: 'Upload error',
        );

        expect(state.canSend, isFalse);
      });

      test('can send when empty', () {
        final state = AttachmentState(
          attachments: [],
          isUploading: false,
          error: null,
        );

        expect(state.canSend, isTrue);
      });
    });

    // ============================================================================
    // DELETION FLOW SCENARIOS
    // ============================================================================

    group('Deletion Flow Scenarios', () {
      test('deleting single attachment from list works', () {
        var state = AttachmentState(
          attachments: [
            const Attachment(
              id: 'att-1',
              filename: 'test.pdf',
              mimeType: 'application/pdf',
              sizeBytes: 1024,
              status: 'completed',
            ),
          ],
          isUploading: false,
        );

        // Remove att-1
        state = state.copyWith(
          attachments: state.attachments
              .where((a) => a.id != 'att-1')
              .toList(),
        );

        expect(state.attachments, isEmpty);
      });

      test('deleting middle attachment from list', () {
        var state = AttachmentState(
          attachments: [
            const Attachment(
              id: 'att-1',
              filename: 'file1.pdf',
              mimeType: 'application/pdf',
              sizeBytes: 1024,
              status: 'completed',
            ),
            const Attachment(
              id: 'att-2',
              filename: 'file2.pdf',
              mimeType: 'application/pdf',
              sizeBytes: 1024,
              status: 'completed',
            ),
            const Attachment(
              id: 'att-3',
              filename: 'file3.pdf',
              mimeType: 'application/pdf',
              sizeBytes: 1024,
              status: 'completed',
            ),
          ],
          isUploading: false,
        );

        // Remove att-2
        state = state.copyWith(
          attachments: state.attachments
              .where((a) => a.id != 'att-2')
              .toList(),
        );

        expect(state.attachments, hasLength(2));
        expect(state.attachments[0].id, equals('att-1'));
        expect(state.attachments[1].id, equals('att-3'));
      });

      test('deleting all attachments from list', () {
        var state = AttachmentState(
          attachments: [
            const Attachment(
              id: 'att-1',
              filename: 'file1.pdf',
              mimeType: 'application/pdf',
              sizeBytes: 1024,
              status: 'completed',
            ),
            const Attachment(
              id: 'att-2',
              filename: 'file2.pdf',
              mimeType: 'application/pdf',
              sizeBytes: 1024,
              status: 'completed',
            ),
          ],
          isUploading: false,
        );

        // Delete both
        state = state.copyWith(
          attachments: state.attachments
              .where((a) => a.id != 'att-1' && a.id != 'att-2')
              .toList(),
        );

        expect(state.attachments, isEmpty);
      });
    });

    // ============================================================================
    // ERROR HANDLING SCENARIOS
    // ============================================================================

    group('Error Handling Scenarios', () {
      test('error state is preserved in attachments', () {
        const att = Attachment(
          id: 'att-1',
          filename: 'test.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 1024,
          status: 'failed',
          error: 'File too large',
        );

        expect(att.isFailed, isTrue);
        expect(att.error, isNotNull);
        expect(att.error, contains('File too large'));
      });

      test('multiple attachments with different statuses', () {
        final attachments = [
          const Attachment(
            id: 'att-1',
            filename: 'completed.pdf',
            mimeType: 'application/pdf',
            sizeBytes: 1024,
            status: 'completed',
          ),
          const Attachment(
            id: 'att-2',
            filename: 'processing.pdf',
            mimeType: 'application/pdf',
            sizeBytes: 1024,
            status: 'processing',
          ),
          const Attachment(
            id: 'att-3',
            filename: 'failed.pdf',
            mimeType: 'application/pdf',
            sizeBytes: 1024,
            status: 'failed',
            error: 'OCR failed',
          ),
        ];

        expect(attachments[0].isCompleted, isTrue);
        expect(attachments[1].isProcessing, isTrue);
        expect(attachments[2].isFailed, isTrue);
      });
    });

    // ============================================================================
    // COMPLETE END-TO-END FLOW TESTS
    // ============================================================================

    group('Complete End-to-End Workflow', () {
      test('full workflow: add → verify → modify → delete → clear', () {
        // Step 1: Create initial attachment
        const attachment = Attachment(
          id: 'att-123',
          filename: 'document.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 5120,
          status: 'completed',
          extractedTextPreview: 'Document content...',
          pageCount: 3,
          wordCount: 250,
          extractionMethod: 'pdf_extraction',
          processingTimeMs: 1234.5,
        );

        var state = AttachmentState(
          attachments: [attachment],
          isUploading: false,
          error: null,
        );

        // Step 2: Verify attachment details
        expect(state.attachments, hasLength(1));
        expect(state.attachments[0].filename, equals('document.pdf'));
        expect(state.attachments[0].sizeDisplay, equals('5.0 KB'));
        expect(state.attachments[0].isCompleted, isTrue);
        expect(state.attachments[0].pageCount, equals(3));

        // Step 3: Verify can send
        expect(state.canSend, isTrue);

        // Step 4: Get attachment IDs for sending
        final attachmentIds = state.attachments.map((a) => a.id).toList();
        expect(attachmentIds, contains('att-123'));

        // Step 5: Delete attachment
        state = state.copyWith(
          attachments: state.attachments
              .where((a) => a.id != 'att-123')
              .toList(),
        );
        expect(state.attachments, isEmpty);

        // Step 6: Clear state
        state = AttachmentState.initial();
        expect(state.attachments, isEmpty);
        expect(state.isUploading, isFalse);
        expect(state.error, isNull);
      });

      test('workflow with multiple files: upload → send → clear', () {
        final att1 = const Attachment(
          id: 'att-1',
          filename: 'file1.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 1024,
          status: 'completed',
        );

        final att2 = const Attachment(
          id: 'att-2',
          filename: 'file2.docx',
          mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          sizeBytes: 2048,
          status: 'completed',
        );

        final att3 = const Attachment(
          id: 'att-3',
          filename: 'file3.txt',
          mimeType: 'text/plain',
          sizeBytes: 512,
          status: 'completed',
        );

        // Step 1: Simulate uploading three files
        var state = AttachmentState(
          attachments: [att1, att2, att3],
          isUploading: false,
          error: null,
        );

        expect(state.attachments, hasLength(3));

        // Step 2: Verify all are ready to send
        expect(state.canSend, isTrue);

        // Step 3: Get IDs to send
        final ids = state.attachments.map((a) => a.id).toList();
        expect(ids.length, equals(3));

        // Step 4: Delete one
        state = state.copyWith(
          attachments: state.attachments
              .where((a) => a.id != 'att-2')
              .toList(),
        );
        expect(state.attachments, hasLength(2));
        expect(state.canSend, isTrue);

        // Step 5: Clear after send
        state = AttachmentState.initial();
        expect(state.attachments, isEmpty);
        expect(state.canSend, isTrue);
      });

      test('workflow with mixed statuses: handle incomplete upload', () {
        final att1 = const Attachment(
          id: 'att-1',
          filename: 'completed.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 1024,
          status: 'completed',
        );

        final att2 = const Attachment(
          id: 'att-2',
          filename: 'processing.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 2048,
          status: 'processing',
        );

        // Step 1: State with mixed statuses
        var state = AttachmentState(
          attachments: [att1, att2],
          isUploading: false,
          error: null,
        );

        // Step 2: Cannot send while processing
        expect(state.canSend, isFalse);

        // Step 3: First completes
        state = state.copyWith(
          attachments: state.attachments.map((a) {
            if (a.id == 'att-2') {
              return a.copyWith(status: 'completed');
            }
            return a;
          }).toList(),
        );

        // Step 4: Now can send
        expect(state.canSend, isTrue);

        // Step 5: Clear
        state = AttachmentState.initial();
        expect(state.attachments, isEmpty);
      });

      test('workflow with error: retry upload', () {
        final failedAtt = const Attachment(
          id: 'att-1',
          filename: 'failed.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 1024,
          status: 'failed',
          error: 'Network error',
        );

        // Step 1: Failed upload
        var state = AttachmentState(
          attachments: [failedAtt],
          isUploading: false,
          error: 'Upload failed: Network error',
        );

        expect(state.canSend, isFalse);
        expect(state.error, contains('Upload failed'));

        // Step 2: Retry - remove failed attachment
        state = state.copyWith(
          attachments: [],
          error: null,
        );

        // Step 3: New upload succeeds
        final newAtt = const Attachment(
          id: 'att-2',
          filename: 'failed.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 1024,
          status: 'completed',
        );

        state = state.copyWith(
          attachments: [newAtt],
        );

        expect(state.canSend, isTrue);
        expect(state.error, isNull);
      });
    });

    // ============================================================================
    // ATTACHMENT DISPLAY TESTS
    // ============================================================================

    group('Attachment Display Data', () {
      test('attachment contains all metadata for display', () {
        const attachment = Attachment(
          id: 'att-1',
          filename: 'document.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 10240,
          status: 'completed',
          extractedTextPreview: 'This is the document...',
          pageCount: 5,
          wordCount: 500,
          extractionMethod: 'pdf_extraction',
          ocrApplied: false,
          processingTimeMs: 2500.0,
          warnings: ['Low contrast on page 2'],
        );

        // All display data available
        expect(attachment.filename, isNotNull);
        expect(attachment.sizeDisplay, equals('10.0 KB'));
        expect(attachment.status, equals('completed'));
        expect(attachment.extractedTextPreview, isNotNull);
        expect(attachment.pageCount, isNotNull);
        expect(attachment.wordCount, isNotNull);
      });

      test('attachment with OCR processing', () {
        const attachment = Attachment(
          id: 'att-1',
          filename: 'scanned.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 5120,
          status: 'completed',
          extractedTextPreview: 'Scanned text...',
          pageCount: 3,
          wordCount: 150,
          extractionMethod: 'ocr',
          ocrApplied: true,
          processingTimeMs: 5000.0,
          warnings: ['OCR confidence < 95% on page 1'],
        );

        expect(attachment.ocrApplied, isTrue);
        expect(attachment.extractionMethod, equals('ocr'));
        expect(attachment.warnings, isNotEmpty);
      });
    });
  });
}
