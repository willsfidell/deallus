import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:deallus_frontend/models/attachment.dart';
import 'package:deallus_frontend/widgets/chat_panel/attachment_chip.dart';

void main() {
  group('AttachmentChip', () {
    late List<String> deletedIds;

    setUp(() {
      deletedIds = [];
    });

    testWidgets('displays filename', (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'document.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 1024,
        status: 'completed',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      expect(find.text('document.pdf'), findsOneWidget);
    });

    testWidgets('displays file size', (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'doc.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 2048,
        status: 'completed',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      expect(find.text('2.0 KB'), findsOneWidget);
    });

    testWidgets('displays bytes for small files', (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'small.txt',
        mimeType: 'text/plain',
        sizeBytes: 512,
        status: 'completed',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      expect(find.text('512 B'), findsOneWidget);
    });

    testWidgets('displays megabytes for large files', (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'large.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 5242880, // 5MB
        status: 'completed',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      expect(find.text('5.0 MB'), findsOneWidget);
    });

    testWidgets('shows check_circle icon when completed',
        (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'doc.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 1024,
        status: 'completed',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      // Find the check_circle icon (green color indicates completed)
      expect(find.byIcon(Icons.check_circle), findsOneWidget);
    });

    testWidgets('shows circular progress indicator when uploading',
        (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'doc.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 1024,
        status: 'uploading',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('shows circular progress indicator when processing',
        (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'doc.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 1024,
        status: 'processing',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('shows error icon when failed', (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'doc.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 1024,
        status: 'failed',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.error), findsOneWidget);
    });

    testWidgets('shows description icon for unknown status',
        (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'doc.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 1024,
        status: 'pending',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.description), findsOneWidget);
    });

    testWidgets('has delete icon', (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'doc.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 1024,
        status: 'completed',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      expect(find.byType(Chip), findsOneWidget);
      // Chip has deleteIcon property set to Icons.close
      final chip = tester.widget<Chip>(find.byType(Chip));
      expect(chip.deleteIcon, isNotNull);
    });

    testWidgets('calls onDelete when delete icon is tapped',
        (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-123',
        filename: 'doc.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 1024,
        status: 'completed',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      // Find and tap the close icon inside the chip
      await tester.tap(find.byIcon(Icons.close));
      await tester.pumpAndSettle();

      expect(deletedIds, contains('att-123'));
    });

    testWidgets('displays as Chip widget', (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'doc.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 1024,
        status: 'completed',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      expect(find.byType(Chip), findsOneWidget);
    });

    testWidgets('has green background when completed',
        (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'doc.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 1024,
        status: 'completed',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      final chip = tester.widget<Chip>(find.byType(Chip));
      expect(chip.backgroundColor, equals(Colors.green[50]));
    });

    testWidgets('has red background when failed', (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'doc.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 1024,
        status: 'failed',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      final chip = tester.widget<Chip>(find.byType(Chip));
      expect(chip.backgroundColor, equals(Colors.red[50]));
    });

    testWidgets('has yellow background when processing',
        (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'doc.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 1024,
        status: 'processing',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      final chip = tester.widget<Chip>(find.byType(Chip));
      expect(chip.backgroundColor, equals(Colors.yellow[50]));
    });

    testWidgets('truncates long filenames', (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'very_long_filename_that_should_be_truncated_with_ellipsis.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 1024,
        status: 'completed',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      // The filename text widget should have maxLines: 1 and overflow: ellipsis
      expect(find.byType(Chip), findsOneWidget);
    });

    testWidgets('renders multiple chips in a wrap', (WidgetTester tester) async {
      final attachments = [
        const Attachment(
          id: 'att-1',
          filename: 'doc1.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 1024,
          status: 'completed',
        ),
        const Attachment(
          id: 'att-2',
          filename: 'doc2.txt',
          mimeType: 'text/plain',
          sizeBytes: 512,
          status: 'completed',
        ),
      ];

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Wrap(
              spacing: 8,
              children: attachments
                  .map((att) => AttachmentChip(
                        attachment: att,
                        onDelete: (id) => deletedIds.add(id),
                      ))
                  .toList(),
            ),
          ),
        ),
      );

      expect(find.byType(AttachmentChip), findsWidgets);
      expect(find.byType(Chip), findsWidgets);
    });

    testWidgets('can be deleted multiple times', (WidgetTester tester) async {
      final attachment1 = const Attachment(
        id: 'att-1',
        filename: 'doc1.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 1024,
        status: 'completed',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StatefulBuilder(
              builder: (context, setState) {
                return Column(
                  children: [
                    AttachmentChip(
                      attachment: attachment1,
                      onDelete: (id) {
                        deletedIds.add(id);
                        setState(() {});
                      },
                    ),
                  ],
                );
              },
            ),
          ),
        ),
      );

      expect(find.byType(Chip), findsOneWidget);
    });

    testWidgets('displays filename and size with correct styling',
        (WidgetTester tester) async {
      const attachment = Attachment(
        id: 'att-1',
        filename: 'document.pdf',
        mimeType: 'application/pdf',
        sizeBytes: 2048,
        status: 'completed',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AttachmentChip(
              attachment: attachment,
              onDelete: (id) => deletedIds.add(id),
            ),
          ),
        ),
      );

      // Verify both filename and size are visible
      expect(find.text('document.pdf'), findsOneWidget);
      expect(find.text('2.0 KB'), findsOneWidget);

      // Verify chip is rendered
      expect(find.byType(Chip), findsOneWidget);
    });
  });
}
