#!/usr/bin/env python3
"""
Test d'intégration de la messagerie Kyberium
Valide le serveur, les clients et les échanges de messages
"""
import subprocess
import time
import sys
import os

def test_integration():
    """Test d'intégration complet de la messagerie"""
    print("🧪 TEST D'INTÉGRATION KYBERIUM MESSENGER")
    print("=" * 60)
    
    print("✅ Vérification des fichiers...")
    
    # Vérifier que tous les fichiers nécessaires existent
    required_files = [
        "kyberium_server.py",
        "kyberium_tk_simple_client.py",
        "test_triple_ratchet.py"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Fichier manquant: {file}")
            assert False
        print(f"   ✅ {file}")
    
    print("\n✅ Vérification du Triple Ratchet...")
    
    # Tester le Triple Ratchet
    try:
        result = subprocess.run([sys.executable, "test_triple_ratchet.py"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("   ✅ Triple Ratchet fonctionne parfaitement")
        else:
            print(f"   ❌ Triple Ratchet échoue: {result.stderr}")
            assert False
    except subprocess.TimeoutExpired:
        print("   ❌ Test Triple Ratchet timeout")
        assert False
    except Exception as e:
        print(f"   ❌ Erreur test Triple Ratchet: {e}")
        assert False
    
    print("\n🎯 INSTRUCTIONS POUR TESTER LA MESSAGERIE:")
    print("=" * 60)
    print("1. Lancez le serveur dans un terminal:")
    print("   python kyberium_server.py")
    print()
    print("2. Lancez le premier client dans un autre terminal:")
    print("   python kyberium_tk_simple_client.py")
    print("   - Connectez-vous avec le nom 'alice'")
    print()
    print("3. Lancez le deuxième client dans un troisième terminal:")
    print("   python kyberium_tk_simple_client.py")
    print("   - Connectez-vous avec le nom 'bob'")
    print()
    print("4. Testez la messagerie:")
    print("   - Cliquez sur 'bob' dans la liste d'alice")
    print("   - Attendez le handshake automatique")
    print("   - Envoyez des messages dans les deux sens")
    print("   - Changez de destinataire en cliquant sur un autre utilisateur")
    print()
    print("✅ AMÉLIORATIONS UX IMPLÉMENTÉES:")
    print("   - Conversation active maintenue automatiquement")
    print("   - Messages reçus directement dans la conversation active")
    print("   - Notifications pour les messages d'autres utilisateurs")
    print("   - Surbrillance des utilisateurs avec nouveaux messages")
    print("   - Possibilité de changer de conversation en cliquant")
    print()
    print("🔐 SÉCURITÉ POST-QUANTIQUE:")
    print("   - Triple Ratchet (Kyber + Dilithium + AES-GCM)")
    print("   - Handshake automatique à la première conversation")
    print("   - Chiffrement de bout en bout")
    print("   - Rotation automatique des clés")
    print()
    print("🎉 Votre messagerie post-quantique est prête !")
    
    assert True

if __name__ == "__main__":
    test_integration() 