# 🛡️ Politique de Sécurité Kyberium

## 1. Objectif et philosophie
Kyberium vise la sécurité post-quantique de niveau militaire, sans compromis : toutes les primitives sont standardisées NIST, aucun dummy, aucune crypto classique, et une politique fail-closed stricte.

## 2. Primitives cryptographiques
- **Échange de clés** : CRYSTALS-Kyber (NIST FIPS 203)
- **Signatures** : CRYSTALS-Dilithium (NIST FIPS 204)
- **Chiffrement symétrique** : AES-GCM, ChaCha20-Poly1305
- **KDF** : SHA-3/SHAKE-256
- **Aucune courbe elliptique, aucun RSA, aucun algorithme non NIST**

## 3. Politique fail-closed
- Toute anomalie (bit-flip, message corrompu, clé incorrecte, edge-case) provoque l’échec immédiat de la session ou du déchiffrement.
- Aucun fallback, aucune récupération silencieuse : la sécurité prime sur la tolérance aux pertes.
- Les tests vérifient la divergence des secrets (fail-closed) et non la levée d’exception.

## 4. Gestion des edge-cases
- **Messages hors-ordre, replay, corruption** : rejetés, aucune récupération automatique.
- **Absence de skipped message keys** : pas de tolérance aux pertes, pour éviter toute faille de synchronisation ou d’attaque par re-synchronisation.
- **Synchronisation stricte** : toute désynchronisation est détectée et provoque l’arrêt sécurisé.

## 5. Tests de robustesse
- **Bit-flip** : tests systématiques sur signature, message, clé publique/privée, ciphertext.
- **Cas limites** : message vide, très long, mauvaise taille, format incorrect.
- **Utilisation exclusive de crypto NIST** : tous les tests utilisent Kyber1024, Dilithium, etc.
- **Aucun dummy** : tous les modules factices ont été supprimés.

## 6. Recommandations avancées
- Pour supporter la tolérance aux pertes (messagerie asynchrone), implémenter la gestion sécurisée des skipped message keys (hors scope actuel, non activé par défaut).
- Pour l’audit, activer les traces internes (root_key, chain_key, message number) en mode debug.
- Pour l’intégration industrielle, suivre les guides de déploiement et d’audit fournis.

## 7. Historique des correctifs de sécurité
- **2025-06** : Suppression totale des dummies, migration full NIST, renforcement fail-closed, bit-flip systématique, documentation exhaustive.
- **2025-07** : Ajout du Triple Ratchet post-quantique, refonte des tests edge-cases, synchronisation stricte.

## 8. Références
- NIST FIPS 203, 204
- Signal Protocol RFC
- Publications sur la sécurité post-quantique 