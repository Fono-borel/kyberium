import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:kyberium_messenger/services/websocket_service.dart';
import 'package:kyberium_messenger/services/chat_service.dart';
import 'package:kyberium_messenger/screens/login_screen.dart';
import 'package:kyberium_messenger/screens/chat_screen.dart';
import 'package:kyberium_messenger/providers/auth_provider.dart';
import 'package:kyberium_messenger/providers/chat_provider.dart';

void main() {
  runApp(const KyberiumMessengerApp());
}

class KyberiumMessengerApp extends StatelessWidget {
  const KyberiumMessengerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => ChatProvider()),
        Provider<WebSocketService>(
          create: (_) => WebSocketService(),
          dispose: (_, service) => service.dispose(),
        ),
        Provider<ChatService>(
          create: (_) => ChatService(),
        ),
      ],
      child: MaterialApp(
        title: 'Kyberium Secure Messenger',
        theme: ThemeData(
          primarySwatch: Colors.blue,
          brightness: Brightness.dark,
          scaffoldBackgroundColor: const Color(0xFF1A1A1A),
          appBarTheme: const AppBarTheme(
            backgroundColor: Color(0xFF2D2D2D),
            foregroundColor: Colors.white,
            elevation: 0,
          ),
          cardTheme: const CardTheme(
            color: Color(0xFF2D2D2D),
            elevation: 2,
          ),
          inputDecorationTheme: const InputDecorationTheme(
            filled: true,
            fillColor: Color(0xFF3D3D3D),
            border: OutlineInputBorder(
              borderSide: BorderSide(color: Colors.blue),
              borderRadius: BorderRadius.all(Radius.circular(12)),
            ),
            enabledBorder: OutlineInputBorder(
              borderSide: BorderSide(color: Colors.grey),
              borderRadius: BorderRadius.all(Radius.circular(12)),
            ),
            focusedBorder: OutlineInputBorder(
              borderSide: BorderSide(color: Colors.blue, width: 2),
              borderRadius: BorderRadius.all(Radius.circular(12)),
            ),
          ),
        ),
        home: const AuthWrapper(),
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        if (authProvider.isConnected) {
          return const ChatScreen();
        } else {
          return const LoginScreen();
        }
      },
    );
  }
} 