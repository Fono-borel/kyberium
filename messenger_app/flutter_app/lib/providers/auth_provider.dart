import 'package:flutter/foundation.dart';
import 'package:kyberium_messenger/services/websocket_service.dart';

class AuthProvider extends ChangeNotifier {
  final WebSocketService _webSocketService = WebSocketService();
  
  bool _isConnected = false;
  String _username = '';
  String _clientId = '';
  String _currentRoom = 'general';

  bool get isConnected => _isConnected;
  String get username => _username;
  String get clientId => _clientId;
  String get currentRoom => _currentRoom;

  Future<void> connect({
    required String username,
    required String serverUrl,
  }) async {
    try {
      await _webSocketService.connect(serverUrl);
      
      // Initialiser la session
      await _initSession(username);
      
      // Effectuer le handshake
      await _performHandshake();
      
      // Rejoindre la salle par défaut
      await _joinRoom(_currentRoom);
      
      _username = username;
      _isConnected = true;
      notifyListeners();
      
    } catch (e) {
      _isConnected = false;
      notifyListeners();
      rethrow;
    }
  }

  Future<void> _initSession(String username) async {
    final initMessage = {
      'type': 'init_session',
      'username': username,
    };
    
    await _webSocketService.send(initMessage);
    
    final response = await _webSocketService.receive();
    final data = response as Map<String, dynamic>;
    
    if (data['type'] == 'session_established') {
      _clientId = data['client_id'];
    } else {
      throw Exception('Échec de l\'initialisation de la session');
    }
  }

  Future<void> _performHandshake() async {
    // Note: Dans une vraie implémentation, nous aurions besoin
    // d'implémenter le chiffrement côté client ou de communiquer
    // avec un service Python via HTTP/WebSocket
    
    final handshakeMessage = {
      'type': 'handshake',
      'client_kem_public': 'dummy_key_for_demo', // Clé factice pour la démo
      'client_sign_public': 'dummy_sign_key_for_demo',
    };
    
    await _webSocketService.send(handshakeMessage);
    
    final response = await _webSocketService.receive();
    final data = response as Map<String, dynamic>;
    
    if (data['type'] != 'handshake_response') {
      throw Exception('Échec du handshake');
    }
  }

  Future<void> _joinRoom(String room) async {
    final message = {
      'type': 'join_room',
      'room': room,
    };
    
    await _webSocketService.send(message);
  }

  void disconnect() {
    _webSocketService.disconnect();
    _isConnected = false;
    _username = '';
    _clientId = '';
    notifyListeners();
  }

  @override
  void dispose() {
    _webSocketService.dispose();
    super.dispose();
  }
} 