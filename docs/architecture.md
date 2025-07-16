# 🏛️ Architecture logicielle Kyberium (mise à jour 2025)

## 1. Vue d’ensemble
Kyberium est structuré pour garantir la sécurité post-quantique, la modularité, l’auditabilité et la robustesse industrielle. L’architecture s’inspire du protocole Signal, mais repose exclusivement sur des primitives NIST (Kyber, Dilithium, AES-GCM, ChaCha20) et une politique fail-closed stricte.

## 2. Séparation des modules
- **kyberium/** : cœur cryptographique (KEM, signatures, symétrique, KDF, Triple Ratchet)
- **messenger_app/** : application de messagerie (serveur, client GUI, gestion des sessions)
- **tests/** : tests unitaires, intégration, sécurité, robustesse
- **docs/** : documentation technique, sécurité, audit

## 3. Logique de sécurité
- **Triple Ratchet post-quantique** : rotation automatique des clés, PFS, synchronisation stricte
- **Fail-closed** : toute anomalie (bit-flip, edge-case, corruption) provoque l’arrêt sécurisé
- **Aucune tolérance aux pertes** : pas de skipped message keys par défaut
- **Auditabilité** : logs, traces internes, documentation exhaustive

## 4. Conformité et évolutivité
- **Conformité NIST** : toutes les primitives sont standardisées
- **Modularité** : chaque composant est isolé, testable, remplaçable
- **Interopérabilité** : API claire, tests multi-plateformes

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