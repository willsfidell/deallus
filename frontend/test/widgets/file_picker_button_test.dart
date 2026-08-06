import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:deallus_frontend/widgets/chat_panel/file_picker_button.dart';

void main() {
  group('FilePickerButton', () {
    late List<List<String>> fileSelections;

    setUp(() {
      fileSelections = [];
    });

    testWidgets('renders with attach_file icon', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FilePickerButton(
              onFilesSelected: (files) => fileSelections.add(files),
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.attach_file), findsOneWidget);
    });

    testWidgets('displays attach file tooltip', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FilePickerButton(
              onFilesSelected: (files) => fileSelections.add(files),
            ),
          ),
        ),
      );

      final iconButton = find.byType(IconButton);
      expect(iconButton, findsOneWidget);
      
      // Verify widget is indeed an IconButton with correct tooltip
      final widget = tester.widget<IconButton>(iconButton);
      expect(widget.tooltip, equals('Attach file'));
    });

    testWidgets('is an icon button widget', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FilePickerButton(
              onFilesSelected: (files) => fileSelections.add(files),
            ),
          ),
        ),
      );

      expect(find.byType(IconButton), findsOneWidget);
    });

    testWidgets('icon button has onPressed handler', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FilePickerButton(
              onFilesSelected: (files) => fileSelections.add(files),
            ),
          ),
        ),
      );

      final widget = tester.widget<IconButton>(find.byType(IconButton));
      expect(widget.onPressed, isNotNull);
    });

    testWidgets('icon button is interactive', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FilePickerButton(
              onFilesSelected: (files) => fileSelections.add(files),
            ),
          ),
        ),
      );

      // Should be able to find and tap the button
      expect(find.byType(IconButton), findsOneWidget);
      
      // Tap the button (we can't verify file picker interaction,
      // but we can verify the button is tappable)
      await tester.tap(find.byType(IconButton));
      await tester.pump();
    });

    testWidgets('can be integrated into a message input row',
        (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: AppBar(title: const Text('Test')),
            body: Row(
              children: [
                FilePickerButton(
                  onFilesSelected: (files) => fileSelections.add(files),
                ),
                const Expanded(
                  child: TextField(
                    decoration: InputDecoration(hintText: 'Message...'),
                  ),
                ),
              ],
            ),
          ),
        ),
      );

      expect(find.byType(FilePickerButton), findsOneWidget);
      expect(find.byType(IconButton), findsWidgets);
      expect(find.byIcon(Icons.attach_file), findsOneWidget);
    });

    testWidgets('accepts onFilesSelected callback', (WidgetTester tester) async {
      bool callbackInvoked = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FilePickerButton(
              onFilesSelected: (files) {
                callbackInvoked = true;
                fileSelections.add(files);
              },
            ),
          ),
        ),
      );

      expect(find.byType(FilePickerButton), findsOneWidget);
      // Callback should not be invoked before interaction
      expect(callbackInvoked, isFalse);
    });

    testWidgets('renders consistently across multiple builds',
        (WidgetTester tester) async {
      final callback = (List<String> files) => fileSelections.add(files);

      // First build
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FilePickerButton(onFilesSelected: callback),
          ),
        ),
      );
      expect(find.byIcon(Icons.attach_file), findsOneWidget);

      // Second build
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FilePickerButton(onFilesSelected: callback),
          ),
        ),
      );
      expect(find.byIcon(Icons.attach_file), findsOneWidget);

      // Third build
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FilePickerButton(onFilesSelected: callback),
          ),
        ),
      );
      expect(find.byIcon(Icons.attach_file), findsOneWidget);
    });

    testWidgets('works with different callback implementations',
        (WidgetTester tester) async {
      final callbacks = <List<String>>[];

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FilePickerButton(
              onFilesSelected: (files) => callbacks.add(files),
            ),
          ),
        ),
      );

      expect(find.byType(FilePickerButton), findsOneWidget);
      // Callbacks should not have been invoked yet
      expect(callbacks, isEmpty);
    });

    testWidgets('widget key can be provided', (WidgetTester tester) async {
      const key = ValueKey('file_picker_button');
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FilePickerButton(
              key: key,
              onFilesSelected: (files) => fileSelections.add(files),
            ),
          ),
        ),
      );

      expect(find.byKey(key), findsOneWidget);
    });

    testWidgets('multiple instances can coexist', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Row(
              children: [
                FilePickerButton(
                  onFilesSelected: (files) => fileSelections.add(files),
                ),
                FilePickerButton(
                  onFilesSelected: (files) => fileSelections.add(files),
                ),
              ],
            ),
          ),
        ),
      );

      expect(find.byType(FilePickerButton), findsWidgets);
      expect(find.byIcon(Icons.attach_file), findsWidgets);
    });

    testWidgets('has enabled state by default', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FilePickerButton(
              onFilesSelected: (files) => fileSelections.add(files),
            ),
          ),
        ),
      );

      final button = tester.widget<IconButton>(find.byType(IconButton));
      // Button should have an onPressed handler (not disabled)
      expect(button.onPressed, isNotNull);
    });
  });
}
