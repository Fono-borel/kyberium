# Kyberium Secure Messenger (Flutter)

[![Licence GNU GPL v3](https://img.shields.io/badge/Licence-GNU%20GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)
[![Conformité GPLv3](https://img.shields.io/badge/Conformit%C3%A9-GPLv3%20Audit-green)](../../docs/audit_conformite_gplv3_kyberium.md)
<img alt="Kyberium Logo" src="../../img/kyberium.png" height="40" style="vertical-align:middle; margin-left:10px;"/>

> **Conformité** :
> Ce logiciel et sa documentation sont placés sous licence GNU GPL v3 (2025, RhaB17369). Toute utilisation, modification ou distribution doit respecter les termes de cette licence. Voir le fichier LICENSE pour les détails et obligations de conformité.

Application mobile de messagerie instantanée sécurisée utilisant le protocole de chiffrement post-quantique Kyberium.

## 🚀 Installation

### Prérequis

- Flutter SDK 3.0.0 ou supérieur
- Dart SDK 3.0.0 ou supérieur
- Serveur Kyberium en cours d'exécution

### Installation

1. **Cloner le projet** (si pas déjà fait) :
```bash
cd messenger_app/flutter_app
```

2. **Installer les dépendances** :
```bash
flutter pub get
```

3. **Lancer l'application** :
```bash
flutter run
```

## 📱 Fonctionnalités

### Interface utilisateur
- ✅ Interface moderne avec thème sombre
- ✅ Écran de connexion sécurisé
- ✅ Chat en temps réel
- ✅ Sélection de salles
- ✅ Messages avec bulles stylisées
- ✅ Indicateurs de statut de connexion

### Communication
- ✅ Connexion WebSocket au serveur Python
- ✅ Gestion des sessions utilisateur
- ✅ Messages en temps réel
- ✅ Gestion des erreurs de connexion

### Sécurité (Démo)
- ⚠️ **Note** : Cette version utilise des clés factices pour la démo
- 🔐 Interface pour le chiffrement post-quantique
- 🔐 Handshake sécurisé (simulé)
- 🔐 Messages chiffrés (simulés)

## 🏗️ Architecture

### Structure des fichiers
```
lib/
├── main.dart                 # Point d'entrée de l'app
├── screens/
│   ├── login_screen.dart     # Écran de connexion
│   └── chat_screen.dart      # Écran de chat principal
├── providers/
│   ├── auth_provider.dart    # Gestion de l'authentification
│   └── chat_provider.dart    # Gestion des messages
├── services/
│   ├── websocket_service.dart # Communication WebSocket
│   └── chat_service.dart     # Service de chat
└── widgets/
    ├── message_bubble.dart   # Bulle de message
    └── room_selector.dart    # Sélecteur de salle
```

### Flux de données
1. **Connexion** : `LoginScreen` → `AuthProvider` → `WebSocketService`
2. **Messages** : `ChatScreen` → `ChatProvider` → `WebSocketService`
3. **Réception** : `WebSocketService` → `ChatProvider` → `ChatScreen`

## 🔧 Configuration

### URL du serveur
Par défaut, l'application se connecte à `ws://localhost:8765`.
Pour changer l'URL :
1. Modifier le champ "URL du serveur" dans l'écran de connexion
2. Ou modifier la valeur par défaut dans `login_screen.dart`

### Thème
Le thème sombre est configuré dans `main.dart`. Pour personnaliser :
```dart
theme: ThemeData(
  primarySwatch: Colors.blue,
  brightness: Brightness.dark,
  // ... autres propriétés
)
```

## 🧪 Test

### Test local
1. Démarrer le serveur Python :
```bash
cd messenger_app
python server.py
```

2. Lancer l'application Flutter :
```bash
cd flutter_app
flutter run
```

3. Se connecter avec un nom d'utilisateur

### Test avec plusieurs clients
1. Lancer plusieurs instances de l'app Flutter
2. Se connecter avec différents noms d'utilisateur
3. Échanger des messages dans différentes salles

## 🔮 Évolutions futures

### Chiffrement réel
Pour implémenter le vrai chiffrement post-quantique :

1. **Option 1** : Compiler Kyberium en WebAssembly
   - Utiliser `dart:ffi` pour appeler les fonctions C
   - Compiler les bibliothèques Python en WASM

2. **Option 2** : Service de chiffrement séparé
   - Créer un microservice Python avec API REST
   - L'app Flutter appelle ce service pour chiffrer/déchiffrer

3. **Option 3** : Implémentation native Dart
   - Réécrire les algorithmes Kyber/Dilithium en Dart
   - Utiliser les bibliothèques crypto Dart

### Fonctionnalités avancées
- [ ] Notifications push
- [ ] Transfert de fichiers
- [ ] Messages vocaux
- [ ] Appels vidéo sécurisés
- [ ] Chiffrement de groupe
- [ ] Sauvegarde sécurisée
- [ ] Synchronisation multi-appareils

## 🐛 Dépannage

### Erreurs courantes

1. **Connexion échouée**
   - Vérifier que le serveur Python est démarré
   - Vérifier l'URL du serveur
   - Vérifier les permissions réseau

2. **Messages non reçus**
   - Vérifier la connexion WebSocket
   - Redémarrer l'application
   - Vérifier les logs du serveur

3. **Interface non responsive**
   - Vérifier les performances du device
   - Réduire le nombre de messages affichés
   - Optimiser le rendu des widgets

### Logs
Les logs sont affichés dans la console Flutter :
```bash
flutter logs
```

## 📄 Licence

Ce projet est sous licence **GNU GPL v3 (2025, RhaB17369)**. Voir le fichier LICENSE pour plus de détails et les obligations de conformité.

## 📚 Documentation

- [Audit de conformité GNU GPL v3](../../docs/audit_conformite_gplv3_kyberium.md)

## 🤝 Contribution

Toute contribution doit respecter la licence GNU GPL v3 et la politique de conformité du projet. Consultez l'[audit de conformité](../../docs/audit_conformite_gplv3_kyberium.md) avant toute soumission.

---

## 🕑 Historique des modifications majeures

- **2025-04** : Migration de la licence MIT vers GNU GPL v3 (RhaB17369), synchronisation documentaire, nettoyage et conformité totale.
- **2024-12** : Ajout du support Triple Ratchet, refonte sécurité, documentation avancée.
- **2024-10** : Première version publique, licence MIT initiale. 

## 📞 Support

Pour toute question, problème ou demande de contact professionnel :

- Ouvrir une issue sur GitHub
- Consulter la documentation
- Tester avec les exemples fournis
- **Contact direct développeur** : maloumbriceharold@gmail.com

---

## 💸 Soutien et financement

Kyberium est un projet open source à vocation scientifique et sécuritaire. Pour toute proposition de financement, sponsoring, mécénat ou partenariat, merci de contacter directement le développeur principal à l’adresse suivante :

**maloumbriceharold@gmail.com**

Un dossier de présentation, des audits techniques et des démonstrations peuvent être fournis sur demande. 