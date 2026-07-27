import 'package:file_picker/file_picker.dart';
import 'package:logger/logger.dart';
import 'package:mime/mime.dart';
import 'dart:io';

import '../config/app_constants.dart';
import '../models/exceptions.dart';

/// Service for file selection and validation
class FileService {
  final Logger _logger = Logger();

  /// Pick files for upload
  Future<List<String>> pickFiles() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'doc', 'docx'],
        allowMultiple: true,
        onFileLoading: (FilePickerStatus status) {
          _logger.d('File loading status: $status');
        },
      );

      if (result == null || result.files.isEmpty) {
        _logger.d('No files selected');
        return [];
      }

      final paths = result.files
          .map((file) => file.path)
          .whereType<String>()
          .toList();

      _logger.d('Selected ${paths.length} files');
      return paths;
    } catch (e) {
      _logger.e('Failed to pick files', error: e);
      throw FileException(
        message: 'Failed to pick files: $e',
        originalException: e,
      );
    }
  }

  /// Pick a single file
  Future<String?> pickSingleFile() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'doc', 'docx'],
        allowMultiple: false,
      );

      if (result == null || result.files.isEmpty) {
        return null;
      }

      return result.files.first.path;
    } catch (e) {
      _logger.e('Failed to pick single file', error: e);
      throw FileException(
        message: 'Failed to pick file: $e',
        originalException: e,
      );
    }
  }

  /// Validate files for upload
  Future<void> validateFiles(List<String> filePaths) async {
    try {
      if (filePaths.isEmpty) {
        throw FileException(message: 'No files selected');
      }

      if (filePaths.length > AppConstants.maxFilesPerMessage) {
        throw FileException(
          message: 'Maximum ${AppConstants.maxFilesPerMessage} files allowed',
        );
      }

      for (final path in filePaths) {
        await _validateFile(path);
      }

      _logger.d('All files validated successfully');
    } catch (e) {
      _logger.e('File validation failed', error: e);
      rethrow;
    }
  }

  /// Validate a single file
  Future<void> _validateFile(String filePath) async {
    try {
      final file = File(filePath);

      // Check if file exists
      if (!await file.exists()) {
        throw FileException(message: 'File does not exist: $filePath');
      }

      // Check file size
      final fileSize = await file.length();
      if (fileSize > AppConstants.maxFileSize) {
        final sizeMB = (fileSize / (1024 * 1024)).toStringAsFixed(2);
        throw FileException(
          message: 'File size ($sizeMB MB) exceeds maximum (5 MB)',
        );
      }

      // Check MIME type
      final mimeType = lookupMimeType(filePath);
      if (mimeType == null || 
          !AppConstants.allowedMimeTypes.contains(mimeType)) {
        throw FileException(
          message: 'File type not allowed: $mimeType',
        );
      }
    } catch (e) {
      _logger.e('Single file validation failed', error: e);
      rethrow;
    }
  }

  /// Get file info
  Future<FileInfo> getFileInfo(String filePath) async {
    try {
      final file = File(filePath);
      final stat = await file.stat();
      final mimeType = lookupMimeType(filePath) ?? 'application/octet-stream';

      return FileInfo(
        path: filePath,
        name: file.path.split('/').last,
        sizeBytes: stat.size,
        mimeType: mimeType,
      );
    } catch (e) {
      _logger.e('Failed to get file info', error: e);
      throw FileException(
        message: 'Failed to get file info: $e',
        originalException: e,
      );
    }
  }

  /// Delete file
  Future<void> deleteFile(String filePath) async {
    try {
      final file = File(filePath);
      if (await file.exists()) {
        await file.delete();
        _logger.d('File deleted: $filePath');
      }
    } catch (e) {
      _logger.e('Failed to delete file', error: e);
      throw FileException(
        message: 'Failed to delete file: $e',
        originalException: e,
      );
    }
  }

  /// Save file (for export/download)
  Future<String> saveFile(String fileName, List<int> content) async {
    try {
      // This will be used for exporting conversations as markdown
      // Platform-specific implementation in export_service.dart
      throw UnimplementedError();
    } catch (e) {
      _logger.e('Failed to save file', error: e);
      throw FileException(
        message: 'Failed to save file: $e',
        originalException: e,
      );
    }
  }
}

/// File information
class FileInfo {
  final String path;
  final String name;
  final int sizeBytes;
  final String mimeType;

  FileInfo({
    required this.path,
    required this.name,
    required this.sizeBytes,
    required this.mimeType,
  });

  String get sizeMB => (sizeBytes / (1024 * 1024)).toStringAsFixed(2);
  
  bool get isImage => mimeType.startsWith('image/');
  bool get isPdf => mimeType == 'application/pdf';
  bool get isWord => mimeType.contains('word') || mimeType.contains('document');
}
