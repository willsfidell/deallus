import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

/// Audio player widget
class AudioPlayerWidget extends StatefulWidget {
  final String audioUrl;
  final Duration duration;
  final VoidCallback? onDownload;

  const AudioPlayerWidget({
    required this.audioUrl,
    this.duration = const Duration(seconds: 0),
    this.onDownload,
    Key? key,
  }) : super(key: key);

  @override
  State<AudioPlayerWidget> createState() => _AudioPlayerWidgetState();
}

class _AudioPlayerWidgetState extends State<AudioPlayerWidget> {
  bool _isPlaying = false;
  Duration _currentPosition = Duration.zero;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            // Play button
            FloatingActionButton.small(
              onPressed: () {
                setState(() {
                  _isPlaying = !_isPlaying;
                });
                // TODO: Implement actual audio playback
              },
              child: Icon(
                _isPlaying ? Icons.pause : Icons.play_arrow,
              ),
            ),
            const SizedBox(width: 12),

            // Progress bar
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SliderTheme(
                    data: SliderThemeData(
                      trackHeight: 4,
                      thumbShape: const RoundSliderThumbShape(
                        enabledThumbRadius: 6,
                      ),
                    ),
                    child: Slider(
                      value: _currentPosition.inSeconds.toDouble(),
                      max: widget.duration.inSeconds.toDouble(),
                      onChanged: (value) {
                        setState(() {
                          _currentPosition =
                              Duration(seconds: value.toInt());
                        });
                      },
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          _formatDuration(_currentPosition),
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                        Text(
                          _formatDuration(widget.duration),
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),

            // Download button
            if (widget.onDownload != null)
              IconButton(
                icon: const Icon(Icons.download),
                onPressed: widget.onDownload,
              ),
          ],
        ),
      ),
    );
  }

  /// Format duration for display
  String _formatDuration(Duration duration) {
    final minutes = duration.inMinutes;
    final seconds = duration.inSeconds.remainder(60);
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }
}
