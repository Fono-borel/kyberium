# 🚀 Guide de Déploiement Kyberium (2025)

## 1. Prérequis
- Système Linux (recommandé), supporté sur Windows/MacOS
- Python 3.11+
- Bibliothèques requises (voir requirements.txt)
- Accès réseau sécurisé (firewall, ports ouverts pour WebSocket)
- Entropie système suffisante (pour la génération de clés post-quantiques)

## 2. Installation
```bash
git clone https://github.com/RhaB17369/kyberium.git
cd kyberium
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Configuration
- Modifier les paramètres réseau dans `messenger_app/kyberium_server.py` (host, port)
- Adapter l’URL du serveur dans `messenger_app/kyberium_gui_client.py`
- Pour usage industriel : configurer le logging, la rotation des logs, la supervision système

## 4. Sécurité opérationnelle
- Exécuter le serveur sur une machine dédiée, isolée du réseau public
- Activer le firewall, limiter les ports ouverts (par défaut 8765)
- Surveiller les logs pour toute anomalie (tentative de replay, corruption, désynchronisation)
- Mettre à jour régulièrement les dépendances (veille sécurité NIST)
- Désactiver tout accès SSH non sécurisé

## 5. Intégration industrielle
- Déployer derrière un reverse proxy sécurisé (Nginx, Apache)
- Utiliser des certificats TLS pour le transport (en plus du chiffrement applicatif)
- Intégrer avec des solutions de supervision (Prometheus, Grafana, ELK)
- Prévoir des audits réguliers (voir docs/SECURITY.md)

## 6. Bonnes pratiques
- Ne jamais exposer les clés privées sur disque ou en clair
- Utiliser des modules matériels (HSM) pour la gestion des secrets en production
- Activer le mode debug uniquement pour l’audit, jamais en production
- Sauvegarder régulièrement la configuration et les logs

## 7. Dépannage
- Voir la section “Dépannage” du README.md
- Consulter les logs détaillés pour toute anomalie
- Vérifier la conformité des versions de Python et des dépendances

## 8. Références
- docs/SECURITY.md, docs/TEST_SUMMARY.md, docs/testing.md
- Guides NIST pour le déploiement de crypto PQC 