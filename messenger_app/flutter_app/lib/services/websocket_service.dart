import 'dart:convert';
import 'dart:async';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketService {
  WebSocketChannel? _channel;
  StreamController<Map<String, dynamic>>? _messageController;
  bool _isConnected = false;

  bool get isConnected => _isConnected;

  Future<void> connect(String url) async {
    try {
      _channel = WebSocketChannel.connect(Uri.parse(url));
      _messageController = StreamController<Map<String, dynamic>>.broadcast();
      
      // Écouter les messages
      _channel!.stream.listen(
        (data) {
          if (data is String) {
            try {
              final message = jsonDecode(data) as Map<String, dynamic>;
              _messageController!.add(message);
            } catch (e) {
              print('Erreur de parsing JSON: $e');
            }
          }
        },
        onError: (error) {
          print('Erreur WebSocket: $error');
          _isConnected = false;
        },
        onDone: () {
          print('Connexion WebSocket fermée');
          _isConnected = false;
        },
      );
      
      _isConnected = true;
    } catch (e) {
      _isConnected = false;
      throw Exception('Impossible de se connecter au serveur: $e');
    }
  }

  Future<void> send(Map<String, dynamic> message) async {
    if (!_isConnected || _channel == null) {
      throw Exception('Non connecté au serveur');
    }
    
    try {
      final jsonMessage = jsonEncode(message);
      _channel!.sink.add(jsonMessage);
    } catch (e) {
      throw Exception('Erreur lors de l\'envoi: $e');
    }
  }

  Future<Map<String, dynamic>> receive() async {
    if (_messageController == null) {
      throw Exception('Service non initialisé');
    }
    
    try {
      return await _messageController!.stream.first;
    } catch (e) {
      throw Exception('Erreur lors de la réception: $e');
    }
  }

  Stream<Map<String, dynamic>> get messageStream {
    if (_messageController == null) {
      throw Exception('Service non initialisé');
    }
    return _messageController!.stream;
  }

  void disconnect() {
    _channel?.sink.close();
    _messageController?.close();
    _isConnected = false;
  }

  void dispose() {
    disconnect();
  }
} 