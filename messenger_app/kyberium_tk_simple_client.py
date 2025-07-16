# ============================================================================
#  Kyberium Secure Messenger - Client Tkinter
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
Client Tkinter Kyberium - messagerie privée 1-to-1, sans salle
"""
import asyncio
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import websockets
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from kyberium.api.session import SessionManager

class KyberiumTkSimpleClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Kyberium Messenger - Client Privé")
        self.root.geometry("800x600")
        
        # État de connexion
        self.connected = False
        self.websocket = None
        self.websocket_loop = None
        self.websocket_thread = None
        
        # Données utilisateur
        self.username = ""
        self.kem_keypair = None
        self.sign_keypair = None
        self.session_self = None  # Session principale pour l'enregistrement
        
        # Données de session
        self.contacts = {}  # username -> {kem_public, sign_public}
        self.sessions = {}  # username -> SessionManager
        self.active_contact = None
        
        # Interface utilisateur
        self.setup_ui()
        
        # Générer les clés au démarrage
        self.generate_keys()

    def generate_keys(self):
        """Génère les clés KEM et de signature pour cet utilisateur"""
        from kyberium.kem.kyber import Kyber1024
        from kyberium.signature.dilithium import DilithiumSignature
        
        kem = Kyber1024()
        signature = DilithiumSignature()
        
        self.kem_keypair = kem.generate_keypair()
        self.sign_keypair = signature.generate_keypair()
        
        print(f"Clés générées - KEM public: {len(self.kem_keypair[0])} bytes, Sign public: {len(self.sign_keypair[0])} bytes")

    def setup_ui(self):
        """Configure l'interface utilisateur avec des améliorations visuelles"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Modern.TFrame', background='#1a1a1a')
        style.configure('Modern.TLabel', background='#1a1a1a', foreground='#ffffff')
        style.configure('Modern.TButton', background='#2d2d2d', foreground='#ffffff')
        
        main_frame = ttk.Frame(self.root, style='Modern.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connexion
        connection_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        connection_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(connection_frame, text="Nom d'utilisateur:", style='Modern.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        self.username_entry = ttk.Entry(connection_frame, width=15)
        self.username_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.connect_btn = ttk.Button(connection_frame, text="🔗 Se connecter", command=self.connect_to_server)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.disconnect_btn = ttk.Button(connection_frame, text="❌ Se déconnecter", command=self.disconnect_from_server)
        self.disconnect_btn.pack(side=tk.LEFT)
        self.status_label = ttk.Label(connection_frame, text="🔴 Déconnecté", style='Modern.TLabel')
        self.status_label.pack(side=tk.RIGHT)
        
        # Split gauche/droite
        content_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Colonne gauche : liste des contacts
        left_frame = ttk.Frame(content_frame, style='Modern.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        ttk.Label(left_frame, text="👥 Utilisateurs connectés", style='Modern.TLabel', font=('Arial', 11, 'bold')).pack(pady=(0, 5))
        self.contacts_list = tk.Listbox(left_frame, bg='#2d2d2d', fg='#ffffff', height=25, activestyle='dotbox')
        self.contacts_list.pack(fill=tk.Y, expand=True)
        self.contacts_list.bind('<<ListboxSelect>>', self.on_contact_selected)
        
        # Colonne droite : chat
        right_frame = ttk.Frame(content_frame, style='Modern.TFrame')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.conversation_title = ttk.Label(right_frame, text="Aucune conversation", style='Modern.TLabel', font=('Arial', 12, 'bold'))
        self.conversation_title.pack(pady=(0, 5))
        self.messages_text = scrolledtext.ScrolledText(
            right_frame,
            wrap=tk.WORD,
            bg='#2d2d2d',
            fg='#ffffff',
            insertbackground='#ffffff',
            font=('Consolas', 10),
            state=tk.DISABLED
        )
        self.messages_text.pack(fill=tk.BOTH, expand=True)
        
        # Configuration des tags pour les messages
        self.messages_text.tag_configure("own_message", foreground="#00ff00")
        self.messages_text.tag_configure("other_message", foreground="#ffffff")
        self.messages_text.tag_configure("system_message", foreground="#ffaa00")
        self.messages_text.tag_configure("notification", foreground="#ffff00", background="#4a4a4a")
        
        # Saisie
        input_frame = ttk.Frame(right_frame, style='Modern.TFrame')
        input_frame.pack(fill=tk.X, pady=(5, 0))
        self.message_entry = ttk.Entry(input_frame, font=('Arial', 10))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry.bind('<Return>', self.send_message)
        self.send_btn = ttk.Button(input_frame, text="📤 Envoyer", command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT)

    def set_controls_state(self, state):
        self.message_entry.config(state=tk.NORMAL if state else tk.DISABLED)
        self.send_btn.config(state=tk.NORMAL if state else tk.DISABLED)
        self.contacts_list.config(state=tk.NORMAL if state else tk.DISABLED)

    def update_status(self, connected, message=""):
        if connected:
            self.status_label.config(text=f"🟢 Connecté {message}")
        else:
            self.status_label.config(text="🔴 Déconnecté")

    def add_message(self, sender, message):
        self.messages_text.config(state=tk.NORMAL)
        if sender == self.username:
            self.messages_text.insert(tk.END, f"👤 {sender} (vous): {message}\n", "own_message")
        else:
            self.messages_text.insert(tk.END, f"👤 {sender}: {message}\n", "other_message")
        self.messages_text.config(state=tk.DISABLED)
        self.messages_text.see(tk.END)

    def add_system_message(self, message):
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.insert(tk.END, f"🔔 {message}\n", "system_message")
        self.messages_text.config(state=tk.DISABLED)
        self.messages_text.see(tk.END)

    def connect_to_server(self):
        self.username = self.username_entry.get().strip()
        if not self.username:
            messagebox.showerror("Erreur", "Veuillez entrer un nom d'utilisateur")
            return
        
        # Créer la session principale avec les clés déjà générées
        self.session_self = SessionManager(use_triple_ratchet=True)
        # Utiliser les clés générées au démarrage au lieu d'en générer de nouvelles
        self.session_self.own_keypair = self.kem_keypair
        self.session_self.own_sign_keypair = self.sign_keypair
        
        # Démarrer le thread WebSocket
        self.websocket_thread = threading.Thread(target=self.websocket_worker, daemon=True)
        self.websocket_thread.start()

    def disconnect_from_server(self):
        self.connected = False
        self.update_status(False)
        self.set_controls_state(False)
        if self.websocket and self.websocket_loop:
            asyncio.run_coroutine_threadsafe(self.websocket.close(), self.websocket_loop)
        self.contacts_list.delete(0, tk.END)
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.delete(1.0, tk.END)
        self.messages_text.config(state=tk.DISABLED)
        self.conversation_title.config(text="Aucune conversation")
        self.active_contact = None
        self.contacts = {}
        self.sessions = {}
        self.session_self = None

    def websocket_worker(self):
        # Créer une nouvelle boucle d'événements pour ce thread
        self.websocket_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.websocket_loop)
        self.websocket_loop.run_until_complete(self.websocket_handler())

    async def websocket_handler(self):
        try:
            self.root.after(0, lambda: self.add_system_message("Connexion au serveur..."))
            async with websockets.connect('ws://localhost:8765') as websocket:
                self.websocket = websocket
                self.connected = True
                self.root.after(0, lambda: self.update_status(True))
                # Enregistrement auprès du serveur
                if self.session_self:
                    register_msg = {
                        "type": "register",
                        "username": self.username,
                        "kem_public": self.session_self.get_public_key().hex(),
                        "sign_public": self.session_self.get_sign_public_key().hex()
                    }
                    await websocket.send(json.dumps(register_msg))
                    self.root.after(0, lambda: self.set_controls_state(True))
                    await self.listen_for_messages()
                else:
                    self.root.after(0, lambda: self.add_system_message("Erreur: Session non initialisée"))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.add_system_message(f"Erreur de connexion: {error_msg}"))
        finally:
            self.connected = False
            self.websocket = None
            self.root.after(0, lambda: self.update_status(False))
            self.root.after(0, lambda: self.set_controls_state(False))

    async def listen_for_messages(self):
        try:
            while self.connected and self.websocket:
                try:
                    message = await self.websocket.recv()
                    data = json.loads(message)
                    if data.get("type") == "user_list":
                        self.root.after(0, lambda: self.update_contacts(data.get("users", [])))
                    elif data.get("type") == "handshake_init":
                        await self.handle_handshake_init(data)
                    elif data.get("type") == "handshake_response":
                        await self.handle_handshake_response(data)
                    elif data.get("type") == "encrypted_message":
                        await self.handle_encrypted_message(data)
                except websockets.exceptions.ConnectionClosed:
                    self.root.after(0, lambda: self.add_system_message("Connexion fermée par le serveur"))
                    break
                except Exception as e:
                    error_msg = str(e)
                    self.root.after(0, lambda: self.add_system_message(f"Erreur de réception: {error_msg}"))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.add_system_message(f"Erreur fatale de réception: {error_msg}"))

    def update_contacts(self, users):
        """Met à jour la liste des contacts et préserve la sélection active"""
        current_selection = None
        if self.contacts_list.size() > 0:
            selection = self.contacts_list.curselection()
            if selection:
                current_selection = self.contacts_list.get(selection[0])
        
        self.contacts_list.delete(0, tk.END)
        self.contacts = {}
        for user in users:
            username = user["username"]
            self.contacts[username] = {
                "kem_public": user["kem_public"],
                "sign_public": user["sign_public"]
            }
            self.contacts_list.insert(tk.END, username)
            
            # Restaurer la sélection si c'était l'utilisateur actif
            if current_selection == username:
                self.contacts_list.selection_set(self.contacts_list.size() - 1)
        
        # Si l'utilisateur actif n'est plus dans la liste, le désélectionner
        if self.active_contact and self.active_contact not in self.contacts:
            self.active_contact = None
            self.conversation_title.config(text="Aucune conversation")
            self.messages_text.config(state=tk.NORMAL)
            self.messages_text.delete(1.0, tk.END)
            self.messages_text.config(state=tk.DISABLED)

    def on_contact_selected(self, event):
        """Gère la sélection d'un contact dans la liste"""
        selection = self.contacts_list.curselection()
        if not selection:
            return
            
        username = self.contacts_list.get(selection[0])
        
        # Si c'est le même utilisateur, ne rien faire
        if self.active_contact == username:
            return
            
        self.active_contact = username
        self.conversation_title.config(text=f"🔒 Conversation privée avec {username}")
        
        # Vider la zone de messages pour la nouvelle conversation
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.delete(1.0, tk.END)
        self.messages_text.config(state=tk.DISABLED)
        
        # Initier le handshake si nécessaire
        if username not in self.sessions:
            self.initiate_handshake(username)
        else:
            self.add_system_message(f"Session chiffrée déjà établie avec {username}")

    def initiate_handshake(self, contact):
        """Initie un handshake Triple Ratchet avec un contact"""
        if contact not in self.contacts:
            self.add_system_message(f"Impossible d'initier le handshake avec {contact}")
            return
        
        # Créer une nouvelle session pour l'initiateur avec les clés du client
        session = SessionManager(use_triple_ratchet=True)
        session.own_keypair = self.kem_keypair
        session.own_sign_keypair = self.sign_keypair
        
        peer_kem_pub = bytes.fromhex(self.contacts[contact]["kem_public"])
        peer_sign_pub = bytes.fromhex(self.contacts[contact]["sign_public"])
        session.set_peer_public_key(peer_kem_pub)
        session.set_peer_sign_public_key(peer_sign_pub)
        
        # Initialiser le Triple Ratchet (côté initiateur)
        handshake = session.triple_ratchet_init(peer_kem_pub, peer_sign_pub)
        self.sessions[contact] = session
        
        handshake_msg = {
            "type": "handshake_init",
            "to": contact,
            "kem_ciphertext": handshake["kem_ciphertext"].hex(),
            "kem_signature": handshake["kem_signature"].hex(),
            "sign_public_key": handshake["sign_public_key"].hex()
        }
        if self.websocket and self.websocket_loop:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps(handshake_msg)),
                self.websocket_loop
            )
        self.add_system_message(f"Handshake initié avec {contact}")

    async def handle_handshake_init(self, data):
        """Gère la réception d'un handshake initié par un autre utilisateur"""
        from_user = data.get("from")
        kem_ciphertext = bytes.fromhex(data["kem_ciphertext"])
        kem_signature = bytes.fromhex(data["kem_signature"])
        sign_public_key = bytes.fromhex(data["sign_public_key"])
        
        # Créer une nouvelle session pour le répondeur avec les clés du client
        session = SessionManager(use_triple_ratchet=True)
        session.own_keypair = self.kem_keypair
        session.own_sign_keypair = self.sign_keypair
        
        peer_kem_pub = bytes.fromhex(self.contacts[from_user]["kem_public"])
        peer_sign_pub = bytes.fromhex(self.contacts[from_user]["sign_public"])
        session.set_peer_public_key(peer_kem_pub)
        session.set_peer_sign_public_key(peer_sign_pub)
        
        # Compléter le handshake (côté répondeur)
        try:
            success = session.triple_ratchet_complete_handshake(
                kem_ciphertext, kem_signature, sign_public_key
            )
            if not success:
                self.add_system_message(f"Échec du handshake avec {from_user}")
                return
        except Exception as e:
            self.add_system_message(f"Erreur lors du handshake avec {from_user}: {e}")
            return
            
        self.sessions[from_user] = session
        self.add_system_message(f"Session chiffrée établie avec {from_user}")

    async def handle_handshake_response(self, data):
        """Gère la réponse à un handshake (normalement pas utilisé dans ce protocole)"""
        from_user = data.get("from")
        self.add_system_message(f"Réponse de handshake reçue de {from_user} (ignorée)")

    async def handle_encrypted_message(self, data):
        """Gère la réception d'un message chiffré"""
        from_user = data.get("from")
        session = self.sessions.get(from_user)
        if not session:
            self.add_system_message(f"Aucune session chiffrée avec {from_user}")
            return
            
        try:
            ciphertext = bytes.fromhex(data["encrypted_data"])
            nonce = bytes.fromhex(data["nonce"])
            signature = bytes.fromhex(data["signature"])
            msg_num = data["msg_num"]
            sign_public_key = bytes.fromhex(data["sign_public_key"])
            
            # Déchiffrer le message avec Triple Ratchet
            decrypted = session.triple_ratchet_decrypt(
                ciphertext, nonce, signature, msg_num, sign_public_key
            )
            if decrypted:
                try:
                    message_data = json.loads(decrypted.decode())
                    sender = message_data.get("sender", from_user)
                    content = message_data.get("content", "")
                except Exception:
                    sender = from_user
                    content = decrypted.decode()
                
                # Si le message vient de l'utilisateur actif, l'afficher directement
                if self.active_contact == from_user:
                    self.root.after(0, lambda: self.add_message(sender, content))
                else:
                    # Si le message vient d'un autre utilisateur, l'afficher avec une notification
                    self.root.after(0, lambda: self.add_message_with_notification(sender, content, from_user))
            else:
                self.root.after(0, lambda: self.add_system_message(f"Impossible de décrypter le message de {from_user}"))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.add_system_message(f"Erreur de déchiffrement: {error_msg}"))

    def add_message_with_notification(self, sender, message, from_user):
        """Ajoute un message avec notification si l'utilisateur n'est pas actif"""
        if self.active_contact != from_user:
            # Ajouter une notification visuelle
            self.messages_text.config(state=tk.NORMAL)
            self.messages_text.insert(tk.END, f"📨 Nouveau message de {from_user} (cliquez sur {from_user} pour voir)\n", "notification")
            self.messages_text.config(state=tk.DISABLED)
            self.messages_text.see(tk.END)
            
            # Mettre en surbrillance l'utilisateur dans la liste
            for i in range(self.contacts_list.size()):
                if self.contacts_list.get(i) == from_user:
                    self.contacts_list.itemconfig(i, {'bg': '#4a4a4a', 'fg': '#ffff00'})
                    break
        else:
            # Message normal si l'utilisateur est actif
            self.add_message(sender, message)

    def send_message(self, event=None):
        """Envoie un message chiffré au contact actif"""
        if not self.connected or not self.websocket or not self.websocket_loop:
            self.add_system_message("Non connecté au serveur")
            return
        if not self.active_contact:
            self.add_system_message("Veuillez sélectionner un destinataire dans la liste des utilisateurs.")
            return
        if self.active_contact not in self.sessions:
            self.add_system_message("Session chiffrée non établie avec ce contact. Veuillez patienter...")
            return
            
        message = self.message_entry.get().strip()
        if not message:
            return
            
        session = self.sessions[self.active_contact]
        message_data = {
            "content": message,
            "sender": self.username
        }
        
        try:
            # Chiffrer le message avec Triple Ratchet
            encrypted_result = session.triple_ratchet_encrypt(
                json.dumps(message_data).encode('utf-8')
            )
            
            encrypted_msg = {
                "type": "encrypted_message",
                "to": self.active_contact,
                "encrypted_data": encrypted_result["ciphertext"].hex(),
                "nonce": encrypted_result["nonce"].hex(),
                "signature": encrypted_result["signature"].hex(),
                "msg_num": encrypted_result["msg_num"],
                "sign_public_key": encrypted_result["sign_public_key"].hex()
            }
            
            if self.websocket and self.websocket_loop:
                asyncio.run_coroutine_threadsafe(
                    self.websocket.send(json.dumps(encrypted_msg)),
                    self.websocket_loop
                )
            self.add_message(self.username, message)
            self.message_entry.delete(0, tk.END)
            
        except Exception as e:
            self.add_system_message(f"Erreur lors du chiffrement: {e}")

    def on_closing(self):
        if self.connected:
            self.disconnect_from_server()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = KyberiumTkSimpleClient(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main() 