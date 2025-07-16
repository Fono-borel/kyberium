#!/usr/bin/env python3
"""
Test des messages privés et de la détection des utilisateurs
"""

import asyncio
import json
import websockets
import sys
import os
from datetime import datetime
import pytest
pytestmark = pytest.mark.asyncio

# Ajouter le chemin racine pour l'import de kyberium
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kyberium.api.session import SessionManager

class TestClient:
    def __init__(self, username):
        self.username = username
        self.websocket = None
        self.session = SessionManager(use_triple_ratchet=True)
        self.session.generate_kem_keypair()
        self.session_established = False
        self.connected = False
        
    async def connect(self):
        """Se connecte au serveur"""
        try:
            self.websocket = await websockets.connect('ws://localhost:8765')
            self.connected = True
            print(f"[{self.username}] Connecté au serveur")
            
            # Établir la session Kyberium
            if await self.establish_session():
                print(f"[{self.username}] Session établie avec succès")
                assert True
            else:
                print(f"[{self.username}] Échec de l'établissement de session")
                assert False
                
        except Exception as e:
            print(f"[{self.username}] Erreur de connexion: {e}")
            assert False
            
    async def establish_session(self):
        """Établit la session Kyberium"""
        try:
            # Envoyer le message d'initialisation
            init_message = {
                "type": "init_session",
                "username": self.username
            }
            await self.websocket.send(json.dumps(init_message))
            
            # Attendre les clés du serveur
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "server_keys":
                # Configurer les clés du serveur
                server_kem_pub = bytes.fromhex(data["server_kem_public"])
                server_sign_pub = bytes.fromhex(data["server_sign_public"])
                
                self.session.set_peer_public_key(server_kem_pub)
                self.session.set_peer_sign_public_key(server_sign_pub)
                
                # Envoyer les clés du client
                client_keys = {
                    "type": "client_keys",
                    "client_kem_public": self.session.get_public_key().hex(),
                    "client_sign_public": self.session.get_sign_public_key().hex()
                }
                await self.websocket.send(json.dumps(client_keys))
                
                # Attendre le handshake
                handshake = await self.websocket.recv()
                handshake_data = json.loads(handshake)
                
                if handshake_data.get("type") == "handshake":
                    # Compléter le handshake
                    success = self.session.triple_ratchet_complete_handshake(
                        bytes.fromhex(handshake_data["kem_ciphertext"]),
                        bytes.fromhex(handshake_data["kem_signature"]),
                        bytes.fromhex(handshake_data["server_sign_public"])
                    )
                    
                    if success:
                        # Envoyer la confirmation du handshake
                        handshake_result = self.session.triple_ratchet_init(
                            server_kem_pub, server_sign_pub
                        )
                        handshake_confirm = {
                            "type": "handshake_complete",
                            "kem_ciphertext": handshake_result["kem_ciphertext"].hex(),
                            "kem_signature": handshake_result["kem_signature"].hex(),
                            "client_sign_public": handshake_result["sign_public_key"].hex()
                        }
                        await self.websocket.send(json.dumps(handshake_confirm))
                        
                        # Attendre la confirmation de session
                        session_confirm = await self.websocket.recv()
                        session_data = json.loads(session_confirm)
                        
                        if session_data.get("type") == "session_established":
                            self.session_established = True
                            assert True
                            
            assert False
            
        except Exception as e:
            print(f"[{self.username}] Erreur lors de l'établissement de session: {e}")
            assert False
            
    async def send_message(self, content, target_user=None, room="general"):
        """Envoie un message"""
        if not self.session_established:
            print(f"[{self.username}] Session non établie")
            assert False
            
        try:
            # Préparer les données du message
            message_data = {
                "content": content,
                "room": room,
                "target_user": target_user
            }
            
            # Chiffrer le message
            encrypted_result = self.session.triple_ratchet_encrypt(
                json.dumps(message_data).encode('utf-8')
            )
            
            # Envoyer le message
            encrypted_msg = {
                "type": "encrypted_message",
                "encrypted_data": encrypted_result["ciphertext"].hex(),
                "nonce": encrypted_result["nonce"].hex(),
                "signature": encrypted_result["signature"].hex(),
                "msg_num": encrypted_result["msg_num"],
                "sign_public_key": encrypted_result["sign_public_key"].hex(),
                "room": room,
                "target_user": target_user
            }
            
            await self.websocket.send(json.dumps(encrypted_msg))
            print(f"[{self.username}] Message envoyé: {content}")
            assert True
            
        except Exception as e:
            print(f"[{self.username}] Erreur lors de l'envoi: {e}")
            assert False
            
    async def listen_for_messages(self, duration=10):
        """Écoute les messages pendant une durée donnée"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < duration:
            try:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                data = json.loads(message)
                
                if data.get("type") == "encrypted_message":
                    # Déchiffrer le message
                    ciphertext = bytes.fromhex(data["encrypted_data"])
                    nonce = bytes.fromhex(data["nonce"])
                    signature = bytes.fromhex(data["signature"])
                    msg_num = data["msg_num"]
                    sign_public_key = bytes.fromhex(data["sign_public_key"])
                    
                    decrypted = self.session.triple_ratchet_decrypt(
                        ciphertext, nonce, signature, msg_num, sign_public_key
                    )
                    
                    if decrypted:
                        try:
                            message_data = json.loads(decrypted.decode())
                            sender = message_data.get("sender", "Inconnu")
                            content = message_data.get("content", "")
                            is_private = data.get("is_private", False)
                            
                            if is_private:
                                print(f"[{self.username}] 🔒 Message privé de {sender}: {content}")
                            else:
                                print(f"[{self.username}] 💬 Message de {sender}: {content}")
                                
                        except json.JSONDecodeError:
                            sender = data.get("sender", "Inconnu")
                            content = decrypted.decode()
                            print(f"[{self.username}] 💬 Message de {sender}: {content}")
                            
                elif data.get("type") == "user_list":
                    users = data.get("users", [])
                    usernames = [user["username"] for user in users]
                    print(f"[{self.username}] 👥 Utilisateurs connectés: {usernames}")
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[{self.username}] Erreur de réception: {e}")
                assert False
                
    async def get_users(self):
        """Demande la liste des utilisateurs"""
        if self.connected:
            await self.websocket.send(json.dumps({"type": "get_users"}))
            
    async def close(self):
        """Ferme la connexion"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            print(f"[{self.username}] Déconnecté")

async def test_private_messages():
    """Test des messages privés"""
    print("🧪 Test des messages privés et de la détection des utilisateurs")
    print("=" * 60)
    
    # Créer deux clients
    client1 = TestClient("Alice")
    client2 = TestClient("Bob")
    
    try:
        # Connecter les clients
        print("\n1. Connexion des clients...")
        success1 = await client1.connect()
        await asyncio.sleep(1)  # Attendre un peu entre les connexions
        success2 = await client2.connect()
        
        if not success1 or not success2:
            print("❌ Échec de la connexion d'un ou plusieurs clients")
            assert False
            
        print("✅ Les deux clients sont connectés")
        
        # Attendre un peu pour que les sessions s'établissent
        await asyncio.sleep(2)
        
        # Demander la liste des utilisateurs
        print("\n2. Demande de la liste des utilisateurs...")
        await client1.get_users()
        await client2.get_users()
        
        # Attendre la réception des listes
        await asyncio.sleep(1)
        
        # Test des messages publics
        print("\n3. Test des messages publics...")
        await client1.send_message("Salut tout le monde !", room="general")
        await asyncio.sleep(1)
        await client2.send_message("Salut Alice !", room="general")
        
        # Écouter les messages pendant 3 secondes
        await asyncio.sleep(3)
        
        # Test des messages privés
        print("\n4. Test des messages privés...")
        await client1.send_message("Message privé pour Bob", target_user="Bob")
        await asyncio.sleep(1)
        await client2.send_message("Réponse privée à Alice", target_user="Alice")
        
        # Écouter les messages pendant 3 secondes
        await asyncio.sleep(3)
        
        # Test de changement de salle
        print("\n5. Test de changement de salle...")
        await client1.send_message("Message dans la salle tech", room="tech")
        await asyncio.sleep(1)
        await client2.send_message("Réponse dans la salle tech", room="tech")
        
        # Écouter les messages pendant 3 secondes
        await asyncio.sleep(3)
        
        print("\n✅ Test terminé avec succès !")
        assert True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        assert False
        
    finally:
        # Fermer les connexions
        await client1.close()
        await client2.close()

if __name__ == "__main__":
    print("🚀 Démarrage du test des messages privés...")
    print("⚠️  Assurez-vous que le serveur Kyberium est démarré sur le port 8765")
    print()
    
    try:
        asyncio.run(test_private_messages())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}") 