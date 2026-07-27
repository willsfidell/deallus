import 'package:flutter/material.dart';

/// Settings action buttons (Save/Cancel)
class SettingsActions extends StatelessWidget {
  final VoidCallback onSave;
  final VoidCallback onCancel;
  final bool isSaving;

  const SettingsActions({
    required this.onSave,
    required this.onCancel,
    this.isSaving = false,
    Key? key,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        // Cancel button
        TextButton(
          onPressed: isSaving ? null : onCancel,
          child: const Text('Cancel'),
        ),
        const SizedBox(width: 12),
        // Save button
        ElevatedButton(
          onPressed: isSaving ? null : onSave,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (isSaving) ...[
                const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
                const SizedBox(width: 8),
              ],
              const Text('Save'),
            ],
          ),
        ),
      ],
    );
  }
}
