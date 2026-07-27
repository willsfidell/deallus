import 'package:flutter/material.dart';

/// API URL input field widget
class ApiUrlInput extends StatefulWidget {
  final TextEditingController controller;
  final ValueChanged<String>? onChanged;
  final String label;
  final String hint;

  const ApiUrlInput({
    required this.controller,
    this.onChanged,
    this.label = 'API URL',
    this.hint = 'e.g., http://localhost:8000',
    Key? key,
  }) : super(key: key);

  @override
  State<ApiUrlInput> createState() => _ApiUrlInputState();
}

class _ApiUrlInputState extends State<ApiUrlInput> {
  String? _errorText;

  /// Validate URL format
  void _validateUrl(String value) {
    if (value.isEmpty) {
      setState(() {
        _errorText = null;
      });
      widget.onChanged?.call(value);
      return;
    }

    try {
      Uri.parse(value);
      if (!value.startsWith('http://') && !value.startsWith('https://')) {
        setState(() {
          _errorText = 'URL must start with http:// or https://';
        });
      } else {
        setState(() {
          _errorText = null;
        });
        widget.onChanged?.call(value);
      }
    } catch (e) {
      setState(() {
        _errorText = 'Invalid URL format';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: widget.controller,
          decoration: InputDecoration(
            labelText: widget.label,
            hintText: widget.hint,
            prefixIcon: const Icon(Icons.link),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
            ),
            errorText: _errorText,
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: const BorderSide(color: Colors.red),
            ),
          ),
          onChanged: _validateUrl,
          keyboardType: TextInputType.url,
        ),
        if (_errorText == null && widget.controller.text.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 8.0),
            child: Row(
              children: [
                const Icon(Icons.check_circle, color: Colors.green, size: 16),
                const SizedBox(width: 8),
                Text(
                  'Valid URL',
                  style: Theme.of(context)
                      .textTheme
                      .bodySmall
                      ?.copyWith(color: Colors.green),
                ),
              ],
            ),
          ),
      ],
    );
  }
}
