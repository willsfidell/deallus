import 'package:logger/logger.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';
import 'dart:io';

import '../config/app_constants.dart';
import '../models/exceptions.dart';

/// Service for audio recording
class AudioService {
  late final AudioRecorder _recorder;
  final Logger _logger = Logger();
  
  String? _currentRecordingPath;
  bool _isRecording = false;

  AudioService() {
    _recorder = AudioRecorder();
  }

  /// Request microphone permission
  Future<bool> requestMicrophonePermission() async {
    try {
      final status = await Permission.microphone.request();
      
      if (status.isDenied) {
        _logger.w('Microphone permission denied');
        return false;
      }
      
      if (status.isPermanentlyDenied) {
        _logger.w('Microphone permission permanently denied');
        openAppSettings();
        return false;
      }
      
      _logger.d('Microphone permission granted');
      return true;
    } catch (e) {
      _logger.e('Failed to request microphone permission', error: e);
      throw AudioException(
        message: 'Failed to request permission: $e',
        originalException: e,
      );
    }
  }

  /// Check if microphone permission is granted
  Future<bool> hasMicrophonePermission() async {
    try {
      final status = await Permission.microphone.status;
      return status.isGranted;
    } catch (e) {
      _logger.e('Failed to check microphone permission', error: e);
      return false;
    }
  }

  /// Start recording audio
  Future<void> startRecording() async {
    try {
      // Check permission
      final hasPermission = await hasMicrophonePermission();
      if (!hasPermission) {
        final granted = await requestMicrophonePermission();
        if (!granted) {
          throw AudioException(
            message: 'Microphone permission not granted',
          );
        }
      }

      // Get temporary directory
      final tempDir = await getTemporaryDirectory();
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      _currentRecordingPath = '${tempDir.path}/audio_$timestamp.wav';

      // Start recording WAV format at 16kHz
      await _recorder.start(
        RecordConfig(
          encoder: AudioEncoder.wav,
          sampleRate: AppConstants.audioSampleRate,
          numChannels: 1, // Mono
          bitRate: 256000,
        ),
        path: _currentRecordingPath!,
      );

      _isRecording = true;
      _logger.d('Recording started: $_currentRecordingPath');
    } catch (e) {
      _logger.e('Failed to start recording', error: e);
      throw AudioException(
        message: 'Failed to start recording: $e',
        originalException: e,
      );
    }
  }

  /// Stop recording and return file path
  Future<String> stopRecording() async {
    try {
      final path = await _recorder.stop();
      _isRecording = false;
      
      if (path == null) {
        throw AudioException(
          message: 'Failed to stop recording',
        );
      }

      _logger.d('Recording stopped: $path');
      return path;
    } catch (e) {
      _logger.e('Failed to stop recording', error: e);
      throw AudioException(
        message: 'Failed to stop recording: $e',
        originalException: e,
      );
    }
  }

  /// Cancel recording and delete file
  Future<void> cancelRecording() async {
    try {
      await _recorder.stop();
      _isRecording = false;

      if (_currentRecordingPath != null) {
        final file = File(_currentRecordingPath!);
        if (await file.exists()) {
          await file.delete();
          _logger.d('Recording file deleted: $_currentRecordingPath');
        }
      }

      _currentRecordingPath = null;
    } catch (e) {
      _logger.e('Failed to cancel recording', error: e);
      throw AudioException(
        message: 'Failed to cancel recording: $e',
        originalException: e,
      );
    }
  }

  /// Get recording duration
  Future<Duration> getRecordingDuration(String filePath) async {
    try {
      final duration = await _recorder.getDuration(filePath);
      return duration ?? Duration.zero;
    } catch (e) {
      _logger.e('Failed to get recording duration', error: e);
      return Duration.zero;
    }
  }

  /// Check if recording is in progress
  bool get isRecording => _isRecording;

  /// Get current recording path
  String? get currentRecordingPath => _currentRecordingPath;

  /// Get file size in MB
  Future<double> getFileSizeMB(String filePath) async {
    try {
      final file = File(filePath);
      if (await file.exists()) {
        final bytes = await file.length();
        return bytes / (1024 * 1024);
      }
      return 0;
    } catch (e) {
      _logger.e('Failed to get file size', error: e);
      return 0;
    }
  }

  /// Delete recording file
  Future<void> deleteRecording(String filePath) async {
    try {
      final file = File(filePath);
      if (await file.exists()) {
        await file.delete();
        _logger.d('Recording file deleted: $filePath');
      }
    } catch (e) {
      _logger.e('Failed to delete recording', error: e);
      throw AudioException(
        message: 'Failed to delete recording: $e',
        originalException: e,
      );
    }
  }

  /// Clean up resources
  Future<void> dispose() async {
    try {
      if (_isRecording) {
        await stopRecording();
      }
      await _recorder.dispose();
      _logger.d('Audio service disposed');
    } catch (e) {
      _logger.e('Failed to dispose audio service', error: e);
    }
  }
}
