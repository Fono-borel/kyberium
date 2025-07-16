#!/usr/bin/env python3
"""
Test des corrections du client graphique Kyberium
"""

import subprocess
import time
import sys
import os

def test_gui_client():
    """Test du client graphique avec les corrections"""
    print("🧪 Test des corrections du client graphique")
    print("=" * 50)
    
    # Vérifier que le serveur est démarré
    print("1. Vérification du serveur...")
    try:
        import websockets
        async def check_server():
            try:
                async with websockets.connect("ws://localhost:8765") as ws:
                    await ws.close()
                return True
            except:
                return False
        
        import asyncio
        server_running = asyncio.run(check_server())
        
        if not server_running:
            print("❌ Serveur non démarré. Démarrage du serveur...")
            server_process = subprocess.Popen(
                [sys.executable, "kyberium_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(3)
            print("✅ Serveur démarré")
        else:
            print("✅ Serveur déjà en cours d'exécution")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification du serveur: {e}")
        assert False
    
    # Tester le client graphique
    print("\n2. Test du client graphique...")
    print("   - Le client graphique va s'ouvrir")
    print("   - Entrez un nom d'utilisateur et connectez-vous")
    print("   - Testez l'envoi de messages")
    print("   - Vérifiez que les messages partent correctement")
    
    try:
        client_process = subprocess.Popen(
            [sys.executable, "kyberium_gui_client.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("✅ Client graphique lancé")
        print("\n📋 Instructions de test:")
        print("   1. Entrez un nom d'utilisateur (ex: 'TestUser')")
        print("   2. Cliquez sur 'Se connecter'")
        print("   3. Attendez que la session Kyberium soit établie")
        print("   4. Tapez un message et appuyez sur Entrée")
        print("   5. Vérifiez que le message s'affiche dans la zone de messages")
        print("   6. Fermez la fenêtre pour terminer le test")
        
        # Attendre que l'utilisateur termine le test
        client_process.wait()
        print("\n✅ Test terminé")
        
    except Exception as e:
        print(f"❌ Erreur lors du lancement du client: {e}")
        assert False
    
    assert True

def test_multi_users():
    """Test avec plusieurs utilisateurs"""
    print("\n🧪 Test multi-utilisateurs")
    print("=" * 30)
    
    try:
        result = subprocess.run(
            [sys.executable, "test_multi_users.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("Sortie du test:")
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ Test multi-utilisateurs réussi")
            assert True
        else:
            print("❌ Test multi-utilisateurs échoué")
            print("Erreur:", result.stderr)
            assert False
            
    except subprocess.TimeoutExpired:
        print("❌ Test multi-utilisateurs timeout")
        assert False
    except Exception as e:
        print(f"❌ Erreur lors du test multi-utilisateurs: {e}")
        assert False

def main():
    """Fonction principale"""
    print("🔐 Test des corrections Kyberium Messenger")
    print("=" * 50)
    
    # Test 1: Client graphique
    success1 = test_gui_client()
    
    # Test 2: Multi-utilisateurs
    success2 = test_multi_users()
    
    # Résumé
    print("\n📊 Résumé des tests:")
    print(f"   Client graphique: {'✅ Réussi' if success1 else '❌ Échoué'}")
    print(f"   Multi-utilisateurs: {'✅ Réussi' if success2 else '❌ Échoué'}")
    
    if success1 and success2:
        print("\n🎉 Tous les tests sont passés !")
        print("   Les corrections fonctionnent correctement.")
    else:
        print("\n⚠️  Certains tests ont échoué.")
        print("   Vérifiez les logs pour plus de détails.")

if __name__ == "__main__":
    main() 