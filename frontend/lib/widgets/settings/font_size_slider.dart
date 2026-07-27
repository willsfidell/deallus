import 'package:flutter/material.dart';

import '../../config/app_constants.dart';

/// Font size slider widget with live preview
class FontSizeSlider extends StatefulWidget {
  final double initialValue;
  final ValueChanged<double> onChanged;

  const FontSizeSlider({
    required this.initialValue,
    required this.onChanged,
    Key? key,
  }) : super(key: key);

  @override
  State<FontSizeSlider> createState() => _FontSizeSliderState();
}

class _FontSizeSliderState extends State<FontSizeSlider> {
  late double _currentValue;

  @override
  void initState() {
    super.initState();
    _currentValue = widget.initialValue;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Slider
        Slider(
          value: _currentValue,
          min: AppConstants.minFontSize,
          max: AppConstants.maxFontSize,
          divisions:
              (AppConstants.maxFontSize - AppConstants.minFontSize).toInt(),
          label: '${_currentValue.toStringAsFixed(1)}pt',
          onChanged: (value) {
            setState(() {
              _currentValue = value;
            });
            widget.onChanged(value);
          },
        ),
        const SizedBox(height: 16),

        // Size range indicators
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              '${AppConstants.minFontSize.toInt()}pt',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            Text(
              '${_currentValue.toStringAsFixed(1)}pt',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            Text(
              '${AppConstants.maxFontSize.toInt()}pt',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
        const SizedBox(height: 20),

        // Live preview
        _buildPreview(context),
      ],
    );
  }

  /// Build live preview section
  Widget _buildPreview(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade300),
        borderRadius: BorderRadius.circular(8),
        color: Colors.grey.shade50,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Preview',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 8),
          Text(
            'This is how your text will look',
            style: TextStyle(fontSize: _currentValue),
          ),
          const SizedBox(height: 8),
          Text(
            'Body Large',
            style: TextStyle(
              fontSize: _currentValue,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Body Small',
            style: TextStyle(
              fontSize: _currentValue * 0.875,
              color: Colors.grey.shade600,
            ),
          ),
        ],
      ),
    );
  }
}
