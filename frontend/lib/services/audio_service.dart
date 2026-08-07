import 'dart:async';
import 'dart:io';
import 'package:record/record.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:logger/logger.dart';
import 'package:path_provider/path_provider.dart';

enum RecordingState {
  idle,
  recording,
  processing,
}

class AudioRecorderService {
  static final AudioRecorderService _instance =
      AudioRecorderService._internal();
  late final AudioRecorder _audioRecorder;
  final Logger _logger = Logger();

  RecordingState _state = RecordingState.idle;
  final _stateController = StreamController<RecordingState>.broadcast();
  final _timerController = StreamController<Duration>.broadcast();
  final _amplitudeController = StreamController<double>.broadcast();

  Timer? _timerTimer;
  Duration _recordingDuration = Duration.zero;
  final Duration _maxRecordingDuration = const Duration(minutes: 2);

  factory AudioRecorderService() {
    return _instance;
  }

  AudioRecorderService._internal() {
    _audioRecorder = AudioRecorder();
  }

  // State management
  RecordingState get state => _state;
  Stream<RecordingState> get stateStream => _stateController.stream;

  Stream<Duration> getTimerStream() => _timerController.stream;
  Stream<double> getAmplitudeStream() => _amplitudeController.stream;

  /// Request microphone permission
  Future<bool> requestPermission() async {
    try {
      final status = await Permission.microphone.request();
      _logger.i('Microphone permission: $status');
      return status.isGranted;
    } catch (e) {
      _logger.e('Error requesting microphone permission: $e');
      return false;
    }
  }

  /// Check if microphone permission is granted
  Future<bool> hasPermission() async {
    try {
      final status = await Permission.microphone.status;
      return status.isGranted;
    } catch (e) {
      _logger.e('Error checking microphone permission: $e');
      return false;
    }
  }

  /// Start recording
  Future<bool> startRecording() async {
    try {
      final hasPermission = await this.hasPermission();
      if (!hasPermission) {
        _logger.w('Microphone permission not granted');
        return false;
      }

      // Check if already recording
      if (_state == RecordingState.recording) {
        _logger.w('Already recording');
        return false;
      }

      // Get temporary directory
      final tempDir = await getTemporaryDirectory();
      final recordingPath =
          '${tempDir.path}/voice_recording_${DateTime.now().millisecondsSinceEpoch}.wav';

      // Start recording - use the file path directly
      await _audioRecorder.start(
        RecordConfig(
          encoder: AudioEncoder.wav,
          bitRate: 128000,
          sampleRate: 16000,
        ),
        path: recordingPath,
      );

      _state = RecordingState.recording;
      _recordingDuration = Duration.zero;
      _stateController.add(_state);

      _logger.i('Recording started: $recordingPath');

      // Start timer for recording duration
      _startTimer();

      return true;
    } catch (e) {
      _logger.e('Error starting recording: $e');
      _state = RecordingState.idle;
      _stateController.add(_state);
      return false;
    }
  }

  /// Stop recording and return file path
  Future<String?> stopRecording() async {
    try {
      if (_state != RecordingState.recording) {
        _logger.w('Not currently recording');
        return null;
      }

      _stopTimer();
      _state = RecordingState.processing;
      _stateController.add(_state);

      final path = await _audioRecorder.stop();
      _logger.i('Recording stopped: $path');

      _state = RecordingState.idle;
      _stateController.add(_state);

      return path;
    } catch (e) {
      _logger.e('Error stopping recording: $e');
      _state = RecordingState.idle;
      _stateController.add(_state);
      return null;
    }
  }

  /// Cancel recording and discard file
  Future<void> cancelRecording() async {
    try {
      _stopTimer();

      await _audioRecorder.stop();

      _state = RecordingState.idle;
      _stateController.add(_state);
      _logger.i('Recording cancelled');
    } catch (e) {
      _logger.e('Error cancelling recording: $e');
      _state = RecordingState.idle;
      _stateController.add(_state);
    }
  }

  /// Start timer for recording duration
  void _startTimer() {
    _timerTimer?.cancel();
    _timerTimer = Timer.periodic(const Duration(milliseconds: 100), (timer) {
      _recordingDuration += const Duration(milliseconds: 100);
      _timerController.add(_recordingDuration);

      // Auto-stop at 2 minutes
      if (_recordingDuration >= _maxRecordingDuration) {
        _logger.i('Recording duration limit reached (2 minutes)');
        stopRecording();
      }
    });
  }

  /// Stop timer
  void _stopTimer() {
    _timerTimer?.cancel();
    _timerTimer = null;
  }

  /// Get current recording duration
  Duration get recordingDuration => _recordingDuration;

  /// Get remaining recording time
  Duration get remainingTime =>
      _maxRecordingDuration - _recordingDuration;

  /// Cleanup resources
  Future<void> dispose() async {
    _timerTimer?.cancel();
    _timerController.close();
    _amplitudeController.close();
    _stateController.close();
    await _audioRecorder.dispose();
  }
}
