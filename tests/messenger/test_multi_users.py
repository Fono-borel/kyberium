#!/usr/bin/env python3
"""
Test de plusieurs utilisateurs connectés simultanément
"""

import asyncio
import json
import websockets
import sys
import os
import time
import threading
import pytest
pytestmark = pytest.mark.asyncio

# Ajouter le chemin racine pour l'import de kyberium
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kyberium.api.session import SessionManager

# Refactor TestUser: move initialization logic from __init__ to a setup method or fixture, and remove __init__ constructor.
class TestUser:
    def __init__(self, username, server_url="ws://localhost:8765"):
        self.username = username
        self.server_url = server_url
        self.websocket = None
        self.session = None
        self.connected = False
        self.messages_received = []
        
    async def connect(self):
        """Se connecte au serveur et établit la session Kyberium"""
        try:
            print(f"🔗 {self.username}: Connexion en cours...")
            self.websocket = await websockets.connect(self.server_url)
            
            # Créer la session Kyberium
            self.session = SessionManager(use_triple_ratchet=True)
            self.session.generate_kem_keypair()
            
            # Message d'initialisation
            init_message = {
                "type": "init_session",
                "username": self.username
            }
            
            await self.websocket.send(json.dumps(init_message))
            print(f"✅ {self.username}: Message d'initialisation envoyé")
            
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
                            self.connected = True
                            print(f"✅ {self.username}: Session Kyberium établie !")
                            return True
                            
            print(f"❌ {self.username}: Échec de l'établissement de session")
            return False
            
        except Exception as e:
            print(f"❌ {self.username}: Erreur de connexion: {e}")
            return False
            
    async def send_message(self, message):
        """Envoie un message chiffré"""
        if not self.connected:
            print(f"❌ {self.username}: Non connecté")
            return False
            
        try:
            # Crypter le message
            encrypted_result = self.session.triple_ratchet_encrypt(message.encode())
            
            message_data = {
                "type": "encrypted_message",
                "encrypted_data": encrypted_result["ciphertext"].hex(),
                "nonce": encrypted_result["nonce"].hex(),
                "signature": encrypted_result["signature"].hex(),
                "msg_num": encrypted_result["msg_num"],
                "sign_public_key": encrypted_result["sign_public_key"].hex(),
                "room": "general"
            }
            
            await self.websocket.send(json.dumps(message_data))
            print(f"📤 {self.username}: Message envoyé: {message}")
            return True
            
        except Exception as e:
            print(f"❌ {self.username}: Erreur d'envoi: {e}")
            return False
            
    async def listen_for_messages(self):
        """Écoute les messages entrants"""
        try:
            while self.connected:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                if data.get("type") == "encrypted_message":
                    try:
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
                            message_data = json.loads(decrypted.decode())
                            sender = data.get("sender", "Inconnu")
                            content = message_data.get("content", "")
                            
                            print(f"📨 {self.username} reçoit de {sender}: {content}")
                            self.messages_received.append({
                                "sender": sender,
                                "content": content,
                                "timestamp": time.time()
                            })
                            
                    except Exception as e:
                        print(f"❌ {self.username}: Erreur de déchiffrement: {e}")
                        
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 {self.username}: Connexion fermée")
        except Exception as e:
            print(f"❌ {self.username}: Erreur d'écoute: {e}")
            
    async def disconnect(self):
        """Se déconnecte du serveur"""
        if self.websocket:
            await self.websocket.close()
        self.connected = False
        print(f"🔌 {self.username}: Déconnecté")

async def test_multi_users():
    """Test avec plusieurs utilisateurs"""
    print("🧪 Test de plusieurs utilisateurs connectés")
    print("=" * 50)
    
    # Créer les utilisateurs de test
    users = [
        TestUser("Alice"),
        TestUser("Bob"),
        TestUser("Charlie")
    ]
    
    try:
        # Connecter tous les utilisateurs
        print("🔗 Connexion des utilisateurs...")
        connection_tasks = [user.connect() for user in users]
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        connected_users = []
        for i, result in enumerate(results):
            if result is True:
                connected_users.append(users[i])
                print(f"✅ {users[i].username} connecté avec succès")
            else:
                print(f"❌ {users[i].username} échec de connexion: {result}")
        
        if len(connected_users) < 2:
            print("❌ Pas assez d'utilisateurs connectés pour le test")
            return
            
        print(f"✅ {len(connected_users)} utilisateurs connectés")
        
        # Démarrer l'écoute des messages pour tous les utilisateurs
        listen_tasks = [user.listen_for_messages() for user in connected_users]
        
        # Attendre un peu pour que les sessions s'établissent
        await asyncio.sleep(2)
        
        # Envoyer des messages de test
        print("\n📤 Envoi de messages de test...")
        
        # Alice envoie un message
        await connected_users[0].send_message("Bonjour tout le monde !")
        await asyncio.sleep(1)
        
        # Bob répond
        await connected_users[1].send_message("Salut Alice ! Comment ça va ?")
        await asyncio.sleep(1)
        
        # Charlie envoie un message
        if len(connected_users) > 2:
            await connected_users[2].send_message("Salut à tous !")
            await asyncio.sleep(1)
        
        # Attendre que les messages soient reçus
        print("⏳ Attente de la réception des messages...")
        await asyncio.sleep(3)
        
        # Afficher les statistiques
        print("\n📊 Statistiques:")
        for user in connected_users:
            print(f"   {user.username}: {len(user.messages_received)} messages reçus")
            
        # Vérifier que les messages ont été reçus
        total_messages = sum(len(user.messages_received) for user in connected_users)
        expected_messages = len(connected_users) * (len(connected_users) - 1)  # Chaque utilisateur envoie à tous les autres
        
        print(f"\n📈 Messages attendus: {expected_messages}")
        print(f"📈 Messages reçus: {total_messages}")
        
        if total_messages >= expected_messages:
            print("✅ Test réussi ! Tous les messages ont été transmis")
        else:
            print("⚠️  Test partiellement réussi - certains messages manquent")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Déconnecter tous les utilisateurs
        print("\n🔌 Déconnexion des utilisateurs...")
        disconnect_tasks = [user.disconnect() for user in users]
        await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        print("✅ Test terminé")

if __name__ == "__main__":
    asyncio.run(test_multi_users()) 