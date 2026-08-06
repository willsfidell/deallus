import 'dart:async';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:logger/logger.dart';

import '../models/attachment.dart';
import 'api_service.dart';

final _logger = Logger();

class AttachmentService {
  final ApiService _apiService;

  AttachmentService(this._apiService);
  
  /// Upload a file and extract text
  Future<Attachment> uploadFile(File file) async {
    try {
      _logger.i('Uploading file: ${file.path}');
      
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          file.path,
          filename: file.path.split('/').last,
        ),
      });
      
      final response = await _apiService.post(
        '/api/attachments/upload',
        data: formData,
      );
      
      final attachment = Attachment.fromJson(response.data!);
      _logger.i('Upload successful: ${attachment.id}');
      return attachment;
    } catch (e) {
      _logger.e('Upload failed: $e');
      rethrow;
    }
  }
  
  /// Get attachment status
  Future<Attachment> getStatus(String attachmentId) async {
    try {
      final response = await _apiService.get(
        '/api/attachments/$attachmentId',
      );
      
      return Attachment.fromJson(response.data!);
    } catch (e) {
      _logger.e('Get status failed: $e');
      rethrow;
    }
  }
  
  /// Delete attachment
  Future<void> deleteAttachment(String attachmentId) async {
    try {
      await _apiService.delete('/api/attachments/$attachmentId');
      _logger.i('Deleted attachment: $attachmentId');
    } catch (e) {
      _logger.e('Delete failed: $e');
      rethrow;
    }
  }
  
  /// Poll status for processing attachments
  Stream<Attachment> pollStatus(
    String attachmentId, {
    int intervalSeconds = 2,
  }) async* {
    while (true) {
      await Future.delayed(Duration(seconds: intervalSeconds));
      
      try {
        final attachment = await getStatus(attachmentId);
        yield attachment;
        
        // Stop polling if completed or failed
        if (attachment.isCompleted || attachment.isFailed) {
          break;
        }
      } catch (e) {
        _logger.e('Polling failed: $e');
        break;
      }
    }
  }
}
