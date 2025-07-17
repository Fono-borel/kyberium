# 📚 Référence API Kyberium (mise à jour 2025)

## 1. Philosophie API
L’API Kyberium expose uniquement des primitives post-quantiques validées (NIST), sans fallback classique ni dummy. Tous les points d’entrée sont conçus pour la sécurité, la simplicité d’intégration et l’auditabilité.

## 2. Points d’entrée principaux
- **SessionManager** (`kyberium.api.session`) : gestion des sessions sécurisées, initialisation, handshake, Triple Ratchet
- **KEM** (`kyberium.kem.kyber.Kyber1024`) : génération de paires de clés, encapsulation, décapsulation
- **Signature** (`kyberium.signature.dilithium.DilithiumSignature`) : génération de clés, signature, vérification
- **Symétrique** (`kyberium.symmetric.aesgcm`, `kyberium.symmetric.chacha20`) : chiffrement/déchiffrement authentifié
- **KDF** (`kyberium.kdf.sha3`) : dérivation de clés, SHA-3/SHAKE-256

## 3. Logique de session et sécurité
- **Initialisation** : échange de clés Kyber, authentification Dilithium
- **Handshake** : vérification mutuelle, encapsulation, signature
- **Triple Ratchet** : rotation automatique des clés, PFS, synchronisation stricte
- **Fail-closed** : toute anomalie = arrêt sécurisé, aucune récupération non sécurisée

## 4. Bonnes pratiques d’utilisation
- Toujours vérifier les retours de chaque opération (aucun fallback)
- Utiliser les modules de test pour valider l’intégration
- Activer le mode debug pour l’audit

---

## 🖼️ Diagrammes et illustrations

### Diagramme de modules
![Diagramme de modules](../img/diagrame%20de%20modules.png)

### Diagramme de séquence
![Diagramme de séquence](../img/diagramme%20de%20sequence.png)

### Diagramme de flux du protocole Kyberium
![Flux du protocole Kyberium](../img/Kyberium_protocol_flux-diagram.svg)

### Diagramme de flux du messenger
![Flux du messenger](../img/Kyberium-messenger_diagram_flux.svg)

### Diagramme global Kyberium
![Diagramme global Kyberium](../img/Kyberium_diagram.svg)

### Diagramme de classes du protocole
![Diagramme de classes du protocole](../img/kyperium_protocol_class_diagram.svg)

### Animation de sécurité
![Animation Kyberium](../img/kyberium-animation.gif) 