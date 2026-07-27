import 'package:flutter/material.dart';

import '../../models/settings.dart';

/// Theme selector with radio buttons
class ThemeSelector extends StatelessWidget {
  final AppThemeMode selectedTheme;
  final ValueChanged<AppThemeMode> onThemeChanged;

  const ThemeSelector({
    required this.selectedTheme,
    required this.onThemeChanged,
    Key? key,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildThemeOption(
          context,
          theme: AppThemeMode.light,
          label: 'Light',
          icon: Icons.light_mode,
        ),
        const SizedBox(height: 12),
        _buildThemeOption(
          context,
          theme: AppThemeMode.dark,
          label: 'Dark',
          icon: Icons.dark_mode,
        ),
        const SizedBox(height: 12),
        _buildThemeOption(
          context,
          theme: AppThemeMode.auto,
          label: 'Auto (System)',
          icon: Icons.brightness_auto,
        ),
      ],
    );
  }

  /// Build individual theme option
  Widget _buildThemeOption(
    BuildContext context, {
    required AppThemeMode theme,
    required String label,
    required IconData icon,
  }) {
    final isSelected = selectedTheme == theme;
    return InkWell(
      onTap: () => onThemeChanged(theme),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          border: Border.all(
            color: isSelected ? Colors.blue : Colors.grey.shade300,
            width: isSelected ? 2 : 1,
          ),
          borderRadius: BorderRadius.circular(8),
          color: isSelected ? Colors.blue.shade50 : Colors.transparent,
        ),
        child: Row(
          children: [
            Radio<AppThemeMode>(
              value: theme,
              groupValue: selectedTheme,
              onChanged: (AppThemeMode? value) {
                if (value != null) {
                  onThemeChanged(value);
                }
              },
            ),
            Icon(icon, size: 20),
            const SizedBox(width: 12),
            Text(
              label,
              style: const TextStyle(fontSize: 16),
            ),
          ],
        ),
      ),
    );
  }
}
