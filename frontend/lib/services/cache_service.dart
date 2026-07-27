import 'package:hive_flutter/hive_flutter.dart';
import 'package:logger/logger.dart';

import '../config/app_constants.dart';
import '../models/audio_recording.dart';
import '../models/exceptions.dart';

/// Local caching service using Hive
class CacheService {
  static late Box<CachedMessage> _messageBox;
  final Logger _logger = Logger();

  /// Initialize Hive and open box
  Future<void> init() async {
    try {
      await Hive.initFlutter();
      
      // Register adapters
      if (!Hive.isAdapterRegistered(CachedMessageAdapter().typeId)) {
        Hive.registerAdapter(CachedMessageAdapter());
      }

      _messageBox = await Hive.openBox<CachedMessage>(
        AppConstants.hiveBoxName,
      );
      
      _logger.i('Cache service initialized');
    } catch (e) {
      _logger.e('Failed to initialize cache service', error: e);
      throw CacheException(
        message: 'Failed to initialize cache: $e',
        originalException: e,
      );
    }
  }

  /// Save message to cache
  Future<void> saveMessage(CachedMessage message) async {
    try {
      await _messageBox.put(message.id, message);
      _logger.d('Message cached: ${message.id}');
    } catch (e) {
      _logger.e('Failed to cache message', error: e);
      throw CacheException(
        message: 'Failed to cache message: $e',
        originalException: e,
      );
    }
  }

  /// Save multiple messages
  Future<void> saveMessages(List<CachedMessage> messages) async {
    try {
      final map = <String, CachedMessage>{};
      for (final msg in messages) {
        map[msg.id] = msg;
      }
      await _messageBox.putAll(map);
      _logger.d('Cached ${messages.length} messages');
    } catch (e) {
      _logger.e('Failed to cache messages', error: e);
      throw CacheException(
        message: 'Failed to cache messages: $e',
        originalException: e,
      );
    }
  }

  /// Get messages for conversation
  List<CachedMessage> getMessagesForConversation(String conversationId) {
    try {
      final messages = _messageBox.values
          .where((m) => m.conversationId == conversationId)
          .toList()
        ..sort((a, b) => b.timestamp.compareTo(a.timestamp));
      
      return messages;
    } catch (e) {
      _logger.e('Failed to retrieve cached messages', error: e);
      throw CacheException(
        message: 'Failed to retrieve cached messages: $e',
        originalException: e,
      );
    }
  }

  /// Get paginated messages for conversation
  List<CachedMessage> getMessagesPaginated(
    String conversationId, {
    int page = 1,
    int pageSize = 20,
  }) {
    try {
      final allMessages = getMessagesForConversation(conversationId);
      
      final startIndex = (page - 1) * pageSize;
      final endIndex = startIndex + pageSize;
      
      if (startIndex >= allMessages.length) {
        return [];
      }
      
      return allMessages.sublist(
        startIndex,
        endIndex > allMessages.length ? allMessages.length : endIndex,
      );
    } catch (e) {
      _logger.e('Failed to retrieve paginated messages', error: e);
      throw CacheException(
        message: 'Failed to retrieve paginated messages: $e',
        originalException: e,
      );
    }
  }

  /// Get total message count for conversation
  int getMessageCount(String conversationId) {
    try {
      return _messageBox.values
          .where((m) => m.conversationId == conversationId)
          .length;
    } catch (e) {
      _logger.e('Failed to get message count', error: e);
      return 0;
    }
  }

  /// Delete message
  Future<void> deleteMessage(String messageId) async {
    try {
      await _messageBox.delete(messageId);
      _logger.d('Message deleted from cache: $messageId');
    } catch (e) {
      _logger.e('Failed to delete message', error: e);
      throw CacheException(
        message: 'Failed to delete message: $e',
        originalException: e,
      );
    }
  }

  /// Delete all messages for conversation
  Future<void> clearConversationCache(String conversationId) async {
    try {
      final keys = _messageBox.values
          .where((m) => m.conversationId == conversationId)
          .map((m) => m.id)
          .toList();
      
      await Future.wait(
        keys.map((k) => _messageBox.delete(k)),
      );
      
      _logger.d('Cleared cache for conversation: $conversationId');
    } catch (e) {
      _logger.e('Failed to clear conversation cache', error: e);
      throw CacheException(
        message: 'Failed to clear cache: $e',
        originalException: e,
      );
    }
  }

  /// Clear entire cache
  Future<void> clearAll() async {
    try {
      await _messageBox.clear();
      _logger.d('Cache completely cleared');
    } catch (e) {
      _logger.e('Failed to clear cache', error: e);
      throw CacheException(
        message: 'Failed to clear cache: $e',
        originalException: e,
      );
    }
  }

  /// Get cache size
  int getCacheSize() {
    return _messageBox.length;
  }

  /// Check if should enforce cache limit
  Future<void> enforceCacheLimit(int maxMessages) async {
    try {
      if (_messageBox.length > maxMessages) {
        final allMessages = _messageBox.values.toList()
          ..sort((a, b) => a.timestamp.compareTo(b.timestamp));
        
        final toDelete = allMessages.length - maxMessages;
        for (int i = 0; i < toDelete; i++) {
          await _messageBox.delete(allMessages[i].id);
        }
        
        _logger.d('Cache limit enforced: removed $toDelete messages');
      }
    } catch (e) {
      _logger.e('Failed to enforce cache limit', error: e);
    }
  }
}

/// Hive adapter for CachedMessage (generated manually)
class CachedMessageAdapter extends TypeAdapter<CachedMessage> {
  @override
  final int typeId = 0;

  @override
  CachedMessage read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{};
    for (int i = 0; i < numOfFields; i++) {
      final fieldId = reader.readByte();
      fields[fieldId] = reader.read();
    }
    return CachedMessage(
      id: fields[0] as String,
      conversationId: fields[1] as String,
      role: fields[2] as String,
      content: fields[3] as String,
      timestamp: fields[4] as DateTime,
      fileIds: (fields[5] as List).cast<String>(),
      audioUrl: fields[6] as String?,
      originalContent: fields[7] as String?,
    );
  }

  @override
  void write(BinaryWriter writer, CachedMessage obj) {
    writer
      ..writeByte(8)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.conversationId)
      ..writeByte(2)
      ..write(obj.role)
      ..writeByte(3)
      ..write(obj.content)
      ..writeByte(4)
      ..write(obj.timestamp)
      ..writeByte(5)
      ..write(obj.fileIds)
      ..writeByte(6)
      ..write(obj.audioUrl)
      ..writeByte(7)
      ..write(obj.originalContent);
  }
}
