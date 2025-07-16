# ============================================================================
#  Kyberium Secure Messenger - Serveur
#  Copyright (C) 2025 RhaB17369
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ============================================================================
#!/usr/bin/env python3
"""
Serveur de messagerie Kyberium - version privée 1-to-1 sans salle
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any
import websockets
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from kyberium.api.session import SessionManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KyberiumMessengerServer:
    def __init__(self):
        # Pour chaque client : websocket, username, clés publiques, etc.
        self.clients: Dict[str, Any] = {}  # client_id -> websocket
        self.user_names: Dict[str, str] = {}  # client_id -> username
        self.public_keys: Dict[str, dict] = {}  # client_id -> {kem_public, sign_public}
        self.client_ids_by_username: Dict[str, str] = {}  # username -> client_id

    async def register_client(self, websocket: Any):
        client_id = str(uuid.uuid4())
        self.clients[client_id] = websocket
        logger.info(f"Nouveau client connecté: {client_id}")
        try:
            # Attendre l'enregistrement du client (username + clés publiques)
            init_message = await websocket.recv()
            data = json.loads(init_message)
            if data.get("type") != "register":
                await websocket.close(1000, "Protocole d'enregistrement invalide")
                return
            username = data.get("username")
            kem_public = data.get("kem_public")
            sign_public = data.get("sign_public")
            if not username or not kem_public or not sign_public:
                await websocket.close(1000, "Données d'enregistrement incomplètes")
                return
            self.user_names[client_id] = username
            self.public_keys[client_id] = {
                "kem_public": kem_public,
                "sign_public": sign_public
            }
            self.client_ids_by_username[username] = client_id
            logger.info(f"Utilisateur enregistré: {username}")
            # Diffuser la liste des utilisateurs à tous
            await self.broadcast_user_list()
            # Boucle principale de réception
            async for message in websocket:
                await self.handle_message(client_id, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client déconnecté: {client_id}")
        except Exception as e:
            logger.error(f"Erreur avec le client {client_id}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.disconnect_client(client_id)

    async def handle_message(self, client_id: str, message: str):
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            if msg_type == "get_users":
                await self.send_user_list(client_id)
            elif msg_type == "handshake_init":
                await self.relay_handshake_init(client_id, data)
            elif msg_type == "handshake_response":
                await self.relay_handshake_response(client_id, data)
            elif msg_type == "encrypted_message":
                await self.relay_encrypted_message(client_id, data)
            else:
                logger.warning(f"Type de message inconnu: {msg_type}")
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}")

    async def relay_handshake_init(self, sender_id: str, data: dict):
        """Relayer l'init du handshake au destinataire"""
        to_username = data.get("to")
        if not to_username:
            return
        target_id = self.client_ids_by_username.get(to_username)
        if not target_id or target_id not in self.clients:
            logger.warning(f"Destinataire {to_username} non trouvé pour handshake_init")
            return
        # Relayer le message tel quel, en ajoutant le nom de l'expéditeur
        relay = dict(data)
        relay["from"] = self.user_names.get(sender_id, "Unknown")
        await self.clients[target_id].send(json.dumps(relay))
        logger.info(f"Handshake init relayé de {self.user_names[sender_id]} à {to_username}")

    async def relay_handshake_response(self, sender_id: str, data: dict):
        """Relayer la réponse de handshake au demandeur"""
        to_username = data.get("to")
        if not to_username:
            return
        target_id = self.client_ids_by_username.get(to_username)
        if not target_id or target_id not in self.clients:
            logger.warning(f"Destinataire {to_username} non trouvé pour handshake_response")
            return
        relay = dict(data)
        relay["from"] = self.user_names.get(sender_id, "Unknown")
        await self.clients[target_id].send(json.dumps(relay))
        logger.info(f"Handshake response relayé de {self.user_names[sender_id]} à {to_username}")

    async def relay_encrypted_message(self, sender_id: str, data: dict):
        """Relayer un message chiffré à un destinataire unique"""
        to_username = data.get("to")
        if not to_username:
            return
        target_id = self.client_ids_by_username.get(to_username)
        if not target_id or target_id not in self.clients:
            logger.warning(f"Destinataire {to_username} non trouvé pour message chiffré")
            return
        relay = dict(data)
        relay["from"] = self.user_names.get(sender_id, "Unknown")
        await self.clients[target_id].send(json.dumps(relay))
        logger.info(f"Message chiffré relayé de {self.user_names[sender_id]} à {to_username}")

    async def send_user_list(self, client_id: str):
        if client_id not in self.clients:
            return
        users = [
            {"username": self.user_names[uid],
             "kem_public": self.public_keys[uid]["kem_public"],
             "sign_public": self.public_keys[uid]["sign_public"]}
            for uid in self.user_names.keys() if uid != client_id
        ]
        message = {"type": "user_list", "users": users}
        await self.clients[client_id].send(json.dumps(message))

    async def broadcast_user_list(self):
        for client_id, websocket in list(self.clients.items()):
            try:
                await self.send_user_list(client_id)
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de la liste des utilisateurs à {client_id}: {e}")

    async def disconnect_client(self, client_id: str):
        if client_id in self.clients:
            del self.clients[client_id]
            if client_id in self.user_names:
                username = self.user_names[client_id]
                del self.user_names[client_id]
                if username in self.client_ids_by_username:
                    del self.client_ids_by_username[username]
            if client_id in self.public_keys:
                del self.public_keys[client_id]
            logger.info(f"Client déconnecté: {client_id}")
            try:
                await self.broadcast_user_list()
            except Exception as e:
                logger.error(f"Erreur lors de la notification de déconnexion: {e}")

async def main():
    server = KyberiumMessengerServer()
    logger.info("Démarrage du serveur Kyberium (messagerie privée 1-to-1, sans salle)")
    async with websockets.serve(server.register_client, "localhost", 8765):
        logger.info("Serveur démarré. En attente de connexions...")
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Arrêt du serveur...") 