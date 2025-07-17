# 🤝 Guide d’Intégration & Exemples Kyberium (2025)

## 1. Initialisation d’une session sécurisée
```python
from kyberium.api.session import SessionManager

# Création du gestionnaire de session
manager = SessionManager()

# Génération des paires de clés (Kyber, Dilithium)
kem_public, kem_private = manager.generate_kem_keypair()
sign_public, sign_private = manager.generate_sign_keypair()

# Enregistrement utilisateur (exemple)
manager.register_user('alice', kem_public, sign_public)
```

## 2. Handshake post-quantique
```python
# Alice initie un handshake avec Bob
handshake_init = manager.initiate_handshake('alice', 'bob')

# Bob répond au handshake
handshake_response = manager.respond_handshake('bob', handshake_init)
```

## 3. Établissement du Triple Ratchet
```python
# Après handshake, initialiser le Triple Ratchet
ratchet = manager.establish_triple_ratchet('alice', 'bob')
```

## 4. Envoi d’un message chiffré
```python
# Chiffrement et envoi
ciphertext = ratchet.encrypt_message(b"Message secret")
# Transmission via WebSocket ou API
```

## 5. Réception et déchiffrement
```python
# Réception et déchiffrement
plaintext = ratchet.decrypt_message(ciphertext)
```

## 6. Bonnes pratiques
- Toujours vérifier les retours de chaque opération
- Ne jamais exposer les clés privées
- Activer le mode debug uniquement pour l’audit
- Utiliser les modules de test pour valider l’intégration

## 7. Références
- docs/api_reference.md, docs/SECURITY.md, docs/testing.md 