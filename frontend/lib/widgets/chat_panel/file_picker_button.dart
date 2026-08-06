import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

typedef OnFilesSelected = Function(List<String> filePaths);

class FilePickerButton extends StatelessWidget {
  const FilePickerButton({
    required this.onFilesSelected,
    super.key,
  });

  final OnFilesSelected onFilesSelected;

  @override
  Widget build(BuildContext context) => IconButton(
        icon: const Icon(Icons.attach_file),
        tooltip: 'Attach file',
        onPressed: _pickFiles,
      );

  Future<void> _pickFiles() async {
    try {
      final result = await FilePicker.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'txt', 'docx'],
        allowMultiple: true,
        onFileLoading: (FilePickerStatus status) {
          // Can show progress if needed
        },
      );

      if (result != null) {
        final paths = result.paths.whereType<String>().toList();
        onFilesSelected(paths);
      }
    } catch (e) {
      // Handle error
    }
  }
}
