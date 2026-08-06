// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'attachment.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Attachment _$AttachmentFromJson(Map<String, dynamic> json) => Attachment(
      id: json['id'] as String,
      filename: json['filename'] as String,
      mimeType: json['mime_type'] as String,
      sizeBytes: (json['size_bytes'] as num).toInt(),
      status: json['status'] as String,
      extractedTextPreview: json['extracted_text_preview'] as String?,
      pageCount: (json['page_count'] as num?)?.toInt(),
      wordCount: (json['word_count'] as num?)?.toInt(),
      extractionMethod: json['extraction_method'] as String?,
      ocrApplied: json['ocr_applied'] as bool?,
      processingTimeMs: (json['processing_time_ms'] as num?)?.toDouble(),
      warnings: (json['warnings'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
      error: json['error'] as String?,
    );

Map<String, dynamic> _$AttachmentToJson(Attachment instance) =>
    <String, dynamic>{
      'id': instance.id,
      'filename': instance.filename,
      'mime_type': instance.mimeType,
      'size_bytes': instance.sizeBytes,
      'status': instance.status,
      'extracted_text_preview': instance.extractedTextPreview,
      'page_count': instance.pageCount,
      'word_count': instance.wordCount,
      'extraction_method': instance.extractionMethod,
      'ocr_applied': instance.ocrApplied,
      'processing_time_ms': instance.processingTimeMs,
      'warnings': instance.warnings,
      'error': instance.error,
    };
