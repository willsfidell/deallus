import 'package:json_annotation/json_annotation.dart';

part 'attachment.g.dart';

@JsonSerializable()
class Attachment {
  final String id;
  final String filename;

  @JsonKey(name: 'mime_type')
  final String mimeType;

  @JsonKey(name: 'size_bytes')
  final int sizeBytes;

  final String status;  // "uploading", "processing", "completed", "failed"

  @JsonKey(name: 'extracted_text_preview')
  final String? extractedTextPreview;

  @JsonKey(name: 'page_count')
  final int? pageCount;

  @JsonKey(name: 'word_count')
  final int? wordCount;

  @JsonKey(name: 'extraction_method')
  final String? extractionMethod;

  @JsonKey(name: 'ocr_applied')
  final bool? ocrApplied;

  @JsonKey(name: 'processing_time_ms')
  final double? processingTimeMs;

  final List<String>? warnings;
  final String? error;

  const Attachment({
    required this.id,
    required this.filename,
    required this.mimeType,
    required this.sizeBytes,
    required this.status,
    this.extractedTextPreview,
    this.pageCount,
    this.wordCount,
    this.extractionMethod,
    this.ocrApplied,
    this.processingTimeMs,
    this.warnings,
    this.error,
  });

  factory Attachment.fromJson(Map<String, dynamic> json) =>
      _$AttachmentFromJson(json);

  Map<String, dynamic> toJson() => _$AttachmentToJson(this);

  bool get isUploading => status == 'uploading';

  bool get isProcessing => status == 'processing';

  bool get isCompleted => status == 'completed';

  bool get isFailed => status == 'failed';

  String get sizeDisplay {
    if (sizeBytes < 1024) {
      return '$sizeBytes B';
    }
    if (sizeBytes < 1024 * 1024) {
      return '${(sizeBytes / 1024).toStringAsFixed(1)} KB';
    }
    return '${(sizeBytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  Attachment copyWith({
    String? id,
    String? filename,
    String? mimeType,
    int? sizeBytes,
    String? status,
    String? extractedTextPreview,
    int? pageCount,
    int? wordCount,
    String? extractionMethod,
    bool? ocrApplied,
    double? processingTimeMs,
    List<String>? warnings,
    String? error,
  }) =>
      Attachment(
        id: id ?? this.id,
        filename: filename ?? this.filename,
        mimeType: mimeType ?? this.mimeType,
        sizeBytes: sizeBytes ?? this.sizeBytes,
        status: status ?? this.status,
        extractedTextPreview: extractedTextPreview ?? this.extractedTextPreview,
        pageCount: pageCount ?? this.pageCount,
        wordCount: wordCount ?? this.wordCount,
        extractionMethod: extractionMethod ?? this.extractionMethod,
        ocrApplied: ocrApplied ?? this.ocrApplied,
        processingTimeMs: processingTimeMs ?? this.processingTimeMs,
        warnings: warnings ?? this.warnings,
        error: error ?? this.error,
      );
}
