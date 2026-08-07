import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../services/audio_service.dart';

class VoiceRecordingWidget extends ConsumerStatefulWidget {
  final Function(String) onTranscriptionComplete;
  final VoidCallback onCancel;
  final VoidCallback onTranscriptionStart;

  const VoiceRecordingWidget({
    required this.onTranscriptionComplete,
    required this.onCancel,
    required this.onTranscriptionStart,
    Key? key,
  }) : super(key: key);

  @override
  ConsumerState<VoiceRecordingWidget> createState() =>
      _VoiceRecordingWidgetState();
}

class _VoiceRecordingWidgetState extends ConsumerState<VoiceRecordingWidget> {
  late AudioRecorderService _audioService;
  bool _isRecording = false;
  Duration _recordingTime = Duration.zero;
  Duration _remainingTime = const Duration(minutes: 2);

  @override
  void initState() {
    super.initState();
    _audioService = AudioRecorderService();

    _audioService.getTimerStream().listen((duration) {
      if (mounted) {
        setState(() {
          _recordingTime = duration;
          _remainingTime = _audioService.remainingTime;
        });
      }
    });

    _audioService.stateStream.listen((state) {
      if (mounted) {
        setState(() {
          _isRecording = state == RecordingState.recording;
        });
      }
    });

    _startRecording();
  }

  Future<void> _startRecording() async {
    final success = await _audioService.startRecording();
    if (!success) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Failed to start recording'),
            duration: Duration(seconds: 2),
          ),
        );
        widget.onCancel();
      }
    }
  }

  Future<void> _stopRecording() async {
    final filePath = await _audioService.stopRecording();
    if (filePath == null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Failed to stop recording'),
            duration: Duration(seconds: 2),
          ),
        );
      }
      return;
    }

    if (mounted) {
      setState(() {
        _isRecording = false;
      });
      widget.onTranscriptionStart();
      widget.onTranscriptionComplete(filePath);
    }
  }

  Future<void> _cancelRecording() async {
    await _audioService.cancelRecording();
    widget.onCancel();
  }

  String _formatDuration(Duration duration) {
    final minutes = duration.inMinutes;
    final seconds = duration.inSeconds % 60;
    return '$minutes:${seconds.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    final totalTime = _formatDuration(const Duration(minutes: 2));
    final currentTime = _formatDuration(_recordingTime);
    final isNearLimit = _recordingTime.inSeconds > 100;

    return Container(
      color: Colors.grey[100],
      padding: const EdgeInsets.all(16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (_isRecording)
                const Padding(
                  padding: EdgeInsets.only(right: 12),
                  child: _PulsingMicrophone(),
                ),
              Text(
                '$currentTime / $totalTime',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: isNearLimit ? Colors.red : Colors.black,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          if (_isRecording)
            const Text(
              'Recording...',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey,
              ),
            ),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              ElevatedButton.icon(
                onPressed: _isRecording ? _cancelRecording : null,
                icon: const Icon(Icons.close),
                label: const Text('Cancel'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red[300],
                  foregroundColor: Colors.white,
                ),
              ),
              ElevatedButton.icon(
                onPressed: _isRecording ? _stopRecording : null,
                icon: const Icon(Icons.stop_circle),
                label: const Text('Stop'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 32,
                    vertical: 16,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _PulsingMicrophone extends StatefulWidget {
  const _PulsingMicrophone({Key? key}) : super(key: key);

  @override
  State<_PulsingMicrophone> createState() => _PulsingMicrophoneState();
}

class _PulsingMicrophoneState extends State<_PulsingMicrophone>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    )..repeat(reverse: true);

    _animation = Tween<double>(begin: 0.5, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: _animation,
      child: const Icon(
        Icons.mic,
        color: Colors.red,
        size: 24,
      ),
    );
  }
}
