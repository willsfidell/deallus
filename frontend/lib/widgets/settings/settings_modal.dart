import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';

import '../../config/app_constants.dart';
import '../../models/settings.dart';
import '../../providers/settings_provider.dart';
import 'api_key_input.dart';
import 'api_url_input.dart';
import 'font_size_slider.dart';
import 'settings_actions.dart';
import 'theme_selector.dart';

/// Main settings modal widget
class SettingsModal extends ConsumerStatefulWidget {
  final VoidCallback? onClose;

  const SettingsModal({
    this.onClose,
    Key? key,
  }) : super(key: key);

  @override
  ConsumerState<SettingsModal> createState() => _SettingsModalState();
}

class _SettingsModalState extends ConsumerState<SettingsModal> {
  late TextEditingController _apiUrlController;
  late TextEditingController _apiKeyController;
  late AppThemeMode _selectedTheme;
  late double _selectedFontSize;
  bool _hasChanges = false;
  final Logger _logger = Logger();

  @override
  void initState() {
    super.initState();
    _apiUrlController = TextEditingController();
    _apiKeyController = TextEditingController();
    _selectedTheme = AppThemeMode.auto;
    _selectedFontSize = 14.0;
    _loadCurrentSettings();
  }

  @override
  void dispose() {
    _apiUrlController.dispose();
    _apiKeyController.dispose();
    super.dispose();
  }

  /// Load current settings into form fields
  void _loadCurrentSettings() {
    final settings = ref.read(settingsProvider);
    settings.whenData((appSettings) {
      setState(() {
        _apiUrlController.text = appSettings.apiUrl;
        _apiKeyController.text = appSettings.apiKey;
        _selectedTheme = appSettings.theme;
        _selectedFontSize = appSettings.fontSize;
      });
    });
  }

  /// Handle settings save
  Future<void> _handleSave() async {
    try {
      _logger.d('Saving settings...');

      final updatedSettings = AppSettings(
        apiUrl: _apiUrlController.text.isNotEmpty 
            ? _apiUrlController.text 
            : AppConstants.defaultApiUrl,
        apiKey: _apiKeyController.text.isNotEmpty 
            ? _apiKeyController.text 
            : '',
        theme: _selectedTheme,
        fontSize: _selectedFontSize,
      );

      // Use the updateSettingsProvider to save all settings at once
      await ref.read(updateSettingsProvider(updatedSettings).future);

      _logger.d('Settings saved successfully');

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Settings saved'),
            duration: Duration(seconds: 2),
          ),
        );
        widget.onClose?.call();
      }
    } catch (e) {
      _logger.e('Failed to save settings', error: e);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error saving settings: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  /// Handle cancel
  void _handleCancel() {
    _loadCurrentSettings();
    widget.onClose?.call();
  }

  /// Track changes
  void _onFieldChanged() {
    setState(() {
      _hasChanges = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    final settingsState = ref.watch(settingsProvider);

    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Settings',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (Navigator.of(context).canPop())
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: _handleCancel,
                  ),
              ],
            ),
            const SizedBox(height: 24),

            // Content
            settingsState.when(
              data: (_) => Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // API URL Section
                  _buildSectionTitle('API Configuration'),
                  const SizedBox(height: 12),
                   ApiUrlInput(
                     controller: _apiUrlController,
                     onChanged: (_) => _onFieldChanged(),
                   ),
                   const SizedBox(height: 16),

                   // API Key Section
                   ApiKeyInput(
                     controller: _apiKeyController,
                     onChanged: (_) => _onFieldChanged(),
                   ),
                  const SizedBox(height: 24),

                  // Theme Section
                  _buildSectionTitle('Theme'),
                  const SizedBox(height: 12),
                  ThemeSelector(
                    selectedTheme: _selectedTheme,
                    onThemeChanged: (theme) {
                      setState(() {
                        _selectedTheme = theme;
                        _onFieldChanged();
                      });
                    },
                  ),
                  const SizedBox(height: 24),

                  // Font Size Section
                  _buildSectionTitle('Font Size'),
                  const SizedBox(height: 12),
                  FontSizeSlider(
                    initialValue: _selectedFontSize,
                    onChanged: (size) {
                      setState(() {
                        _selectedFontSize = size;
                        _onFieldChanged();
                      });
                    },
                  ),
                ],
              ),
              loading: () => Center(
                child: Column(
                  children: [
                    const CircularProgressIndicator(),
                    const SizedBox(height: 16),
                    const Text('Loading settings...'),
                  ],
                ),
              ),
              error: (error, st) => Center(
                child: Column(
                  children: [
                    const Icon(Icons.error, color: Colors.red),
                    const SizedBox(height: 16),
                    Text('Error loading settings: $error'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 32),

            // Actions
            SettingsActions(
              onSave: _handleSave,
              onCancel: _handleCancel,
              isSaving: false,
            ),
          ],
        ),
      ),
    );
  }

  /// Build section title widget
  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        color: Colors.grey,
      ),
    );
  }
}
