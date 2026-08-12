import 'dart:io';
import 'package:dio/dio.dart';
import 'package:logger/logger.dart';

class TranscriptionService {
  static final TranscriptionService _instance =
      TranscriptionService._internal();

  final Logger _logger = Logger();
  late final Dio _dio;
  final String _baseUrl = 'http://localhost:8000';

  factory TranscriptionService() {
    return _instance;
  }

  TranscriptionService._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 70),
      receiveTimeout: const Duration(seconds: 70),
    ));
  }

  Future<String> transcribeAudio(File audioFile, String apiKey) async {
    try {
      _logger.i('Starting transcription for ${audioFile.path}');

      if (!await audioFile.exists()) {
        throw Exception('Audio file not found: ${audioFile.path}');
      }

      final fileSize = await audioFile.length();
      final fileSizeMB = fileSize / (1024 * 1024);
      _logger.i('Audio file size: ${fileSizeMB.toStringAsFixed(2)}MB');

      // Create multipart form data with explicit MIME type
      final multipartFile = await MultipartFile.fromFile(
        audioFile.path,
        filename: 'recording.wav',
        contentType: DioMediaType.parse('audio/wav'),
      );
      
      _logger.i('Multipart file - Name: ${multipartFile.filename}, Size: ${multipartFile.length} bytes, Content-Type: ${multipartFile.contentType}');
      
      FormData formData = FormData.fromMap({
        'file': multipartFile,
      });

      _logger.i('Sending transcription request to $_baseUrl/api/transcribe');
      _logger.d('Request headers: X-API-Key: ${apiKey.substring(0, 10)}...');

      final response = await _dio.post(
        '/api/transcribe',
        data: formData,
        options: Options(
          headers: {
            'X-API-Key': apiKey,
          },
        ),
      );

      _logger.i('Transcription response: ${response.statusCode}');

      if (response.statusCode == 200) {
        final data = response.data;
        final text = data['text'] as String?;
        
        if (text == null || text.isEmpty) {
          throw Exception('No text in transcription response');
        }

        _logger.i('Transcription successful: ${text.length} characters');
        return text;
      } else {
        throw Exception(
          'Transcription failed: ${response.statusCode}',
        );
      }
    } on DioException catch (e) {
      _logger.e('Dio error: ${e.message}');
      _logger.e('Response status: ${e.response?.statusCode}');
      _logger.e('Response data: ${e.response?.data}');
      
      if (e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.receiveTimeout) {
        throw Exception('Transcription timeout - server took too long to respond');
      } else if (e.response?.statusCode == 400) {
        final errorDetail = e.response?.data['detail'] ?? 'Unknown error';
        _logger.e('400 Error detail: $errorDetail');
        throw Exception('Invalid request: $errorDetail');
      } else if (e.response?.statusCode == 413) {
        throw Exception('Audio file too large (max 10MB)');
      } else if (e.response?.statusCode == 500) {
        throw Exception('Transcription failed on server');
      } else if (e.response?.statusCode == 503) {
        throw Exception('Transcription service unavailable');
      } else {
        throw Exception('Transcription failed: ${e.message}');
      }
    } catch (e) {
      _logger.e('Transcription error: $e');
      rethrow;
    }
  }
}
