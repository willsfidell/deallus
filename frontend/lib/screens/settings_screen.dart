import 'package:flutter/material.dart';

import '../widgets/settings/settings_modal.dart';

/// Settings screen wrapped in a modal dialog
class SettingsScreen extends StatelessWidget {
  const SettingsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      contentPadding: EdgeInsets.zero,
      content: SizedBox(
        width: MediaQuery.of(context).size.width * 0.5,
        child: SettingsModal(
          onClose: () => Navigator.of(context).pop(),
        ),
      ),
    );
  }

  /// Show settings screen as a dialog
  static Future<void> show(BuildContext context) {
    return showDialog(
      context: context,
      builder: (context) => const SettingsScreen(),
      barrierDismissible: false,
    );
  }
}
