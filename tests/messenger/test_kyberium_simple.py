#!/usr/bin/env python3
"""
Test simple du protocole Kyberium pour identifier les problèmes
"""

import asyncio
import json
import websockets
import sys
import os
import pytest
pytestmark = pytest.mark.asyncio

# Ajouter le chemin racine pour l'import de kyberium
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kyberium.api.session import SessionManager

async def test_kyberium_connection():
    """Test de connexion Kyberium simple."""
    server_url = "ws://localhost:8765"
    
    print("🔐 Test de connexion Kyberium simple")
    print(f"📡 Tentative de connexion à: {server_url}")
    print("=" * 50)
    
    try:
        # Connexion au serveur
        print("🔄 Connexion en cours...")
        async with websockets.connect(server_url) as websocket:
            print("✅ Connexion établie !")
            
            # Créer la session Kyberium
            print("🔑 Création de la session Kyberium...")
            session = SessionManager(use_triple_ratchet=True)
            session.generate_kem_keypair()
            print("✅ Session Kyberium créée")
            
            # Test 1: Message d'initialisation
            print("\n📤 Test 1: Message d'initialisation")
            init_message = {
                "type": "init_session",
                "username": "TestUser"
            }
            
            await websocket.send(json.dumps(init_message))
            print("✅ Message d'initialisation envoyé")
            
            # Attendre la réponse
            print("⏳ Attente de la réponse d'initialisation...")
            response = await websocket.recv()
            print(f"📨 Réponse reçue: {response}")
            
            # Parser la réponse
            data = json.loads(response)
            print(f"📋 Données parsées: {data}")
            
            if data.get("type") == "server_keys":
                print("✅ Clés serveur reçues")
                
                # Configurer les clés du serveur
                server_kem_pub = bytes.fromhex(data["server_kem_public"])
                server_sign_pub = bytes.fromhex(data["server_sign_public"])
                
                session.set_peer_public_key(server_kem_pub)
                session.set_peer_sign_public_key(server_sign_pub)
                print("✅ Clés serveur configurées")
                
                # Envoyer les clés du client
                print("\n📤 Envoi des clés client...")
                client_keys = {
                    "type": "client_keys",
                    "client_kem_public": session.get_public_key().hex(),
                    "client_sign_public": session.get_sign_public_key().hex()
                }
                
                await websocket.send(json.dumps(client_keys))
                print("✅ Clés client envoyées")
                
                # Attendre le handshake
                print("⏳ Attente du handshake...")
                handshake = await websocket.recv()
                print(f"📨 Handshake reçu: {handshake}")
                
                handshake_data = json.loads(handshake)
                if handshake_data.get("type") == "handshake":
                    print("✅ Handshake reçu")
                    
                    # Compléter le handshake
                    success = session.triple_ratchet_complete_handshake(
                        bytes.fromhex(handshake_data["kem_ciphertext"]),
                        bytes.fromhex(handshake_data["kem_signature"]),
                        bytes.fromhex(handshake_data["server_sign_public"])
                    )
                    
                    if success:
                        # Envoyer la confirmation du handshake
                        handshake_result = session.triple_ratchet_init(
                            server_kem_pub, server_sign_pub
                        )
                        handshake_confirm = {
                            "type": "handshake_complete",
                            "kem_ciphertext": handshake_result["kem_ciphertext"].hex(),
                            "kem_signature": handshake_result["kem_signature"].hex(),
                            "client_sign_public": handshake_result["sign_public_key"].hex()
                        }
                        
                        await websocket.send(json.dumps(handshake_confirm))
                        print("✅ Confirmation du handshake envoyée")
                        
                        # Attendre la confirmation de session
                        session_confirm = await websocket.recv()
                        session_data = json.loads(session_confirm)
                        
                        if session_data.get("type") == "session_established":
                            print("✅ Session Kyberium établie avec succès !")
                            print("🔐 Protocole post-quantique actif")
                            assert True
                        else:
                            print(f"❌ Échec de l'établissement de session")
                            assert False
                    else:
                        print(f"❌ Échec du handshake Triple Ratchet")
                        assert False
                else:
                    print(f"❌ Type de handshake inattendu: {handshake_data.get('type')}")
                    assert False
            else:
                print(f"❌ Type de réponse inattendu: {data.get('type')}")
                assert False
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connexion fermée: {e}")
        print(f"   Code: {e.code}")
        print(f"   Raison: {e.reason}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_kyberium_connection()) 