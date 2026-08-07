import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:logger/logger.dart';

class TranscriptionService {
  static final TranscriptionService _instance =
      TranscriptionService._internal();

  final Logger _logger = Logger();
  final String _baseUrl = 'http://localhost:8000';

  factory TranscriptionService() {
    return _instance;
  }

  TranscriptionService._internal();

  Future<String> transcribeAudio(File audioFile, String apiKey) async {
    try {
      _logger.i('Starting transcription for ${audioFile.path}');

      if (!await audioFile.exists()) {
        throw Exception('Audio file not found: ${audioFile.path}');
      }

      final fileSize = await audioFile.length();
      final fileSizeMB = fileSize / (1024 * 1024);
      _logger.i('Audio file size: ${fileSizeMB.toStringAsFixed(2)}MB');

      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$_baseUrl/api/transcribe'),
      );

      request.files.add(
        http.MultipartFile(
          'file',
          audioFile.openRead(),
          fileSize,
          filename: 'recording.wav',
        ),
      );

      request.headers['X-API-Key'] = apiKey;

      _logger.i('Sending transcription request to $_baseUrl/api/transcribe');
      final streamedResponse = await request.send().timeout(
        const Duration(seconds: 70),
        onTimeout: () {
          _logger.e('Transcription request timeout');
          throw Exception(
              'Transcription timeout - server took too long to respond');
        },
      );

      final response = await http.Response.fromStream(streamedResponse);

      _logger.i('Transcription response: ${response.statusCode}');

      if (response.statusCode == 200) {
        final Map<String, dynamic> json = jsonDecode(response.body);

        final text = json['text'] as String?;
        if (text == null || text.isEmpty) {
          throw Exception('No text in transcription response');
        }

        _logger.i('Transcription successful: ${text.length} characters');
        return text;
      } else if (response.statusCode == 400) {
        throw Exception('Invalid audio format or missing file');
      } else if (response.statusCode == 413) {
        throw Exception('Audio file too large (max 10MB)');
      } else if (response.statusCode == 500) {
        throw Exception('Transcription failed on server');
      } else if (response.statusCode == 503) {
        throw Exception('Transcription service unavailable');
      } else {
        throw Exception(
          'Transcription failed: ${response.statusCode} - ${response.body}',
        );
      }
    } catch (e) {
      _logger.e('Transcription error: $e');
      rethrow;
    }
  }
}
