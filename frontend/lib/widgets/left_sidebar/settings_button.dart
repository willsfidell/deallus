import 'package:flutter/material.dart';

/// Settings button widget (bottom of sidebar)
class SettingsButton extends StatelessWidget {
  final VoidCallback onPressed;

  const SettingsButton({
    required this.onPressed,
    Key? key,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: onPressed,
        icon: const Icon(Icons.settings),
        label: const Text('Settings'),
        style: ElevatedButton.styleFrom(
          padding: const EdgeInsets.symmetric(vertical: 12),
          backgroundColor: Colors.grey.shade200,
          foregroundColor: Colors.black87,
        ),
      ),
    );
  }
}
