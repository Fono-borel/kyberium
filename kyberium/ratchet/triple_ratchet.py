# ============================================================================
#  Kyberium - Post-Quantum Cryptography Library
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

from kyberium.kem.kyber import Kyber1024
from kyberium.kdf.sha3 import SHA3KDF
from kyberium.signature.dilithium import DilithiumSignature
from kyberium.symmetric.aesgcm import AESGCMCipher
import os

class TripleRatchet:
    """
    Abstraction Triple Ratchet post-quantique :
    - Double Ratchet (rotation de clés symétriques + KDF)
    - Authentification forte (signature post-quantique)
    - Gestion des identités et de la PFS
    """
    def __init__(self,
                 kem=None,
                 kdf=None,
                 signature=None,
                 symmetric=None,
                 symmetric_key_size=32,
                 own_kem_keypair=None):
        self.kem = kem or Kyber1024()
        self.kdf = kdf or SHA3KDF()
        self.signature = signature or DilithiumSignature()
        self.symmetric = symmetric or AESGCMCipher(key_size=symmetric_key_size)
        # États internes
        self.DHs = own_kem_keypair  # Clé Diffie-Hellman locale (KEM)
        self.DHr = None  # Clé Diffie-Hellman du pair
        self.root_key = None
        self.send_chain_key = None
        self.recv_chain_key = None
        self.send_message_number = 0
        self.recv_message_number = 0
        self.skipped_message_keys = {}
        self.own_sign_keypair = self.signature.generate_keypair()
        self.peer_sign_public_key = None
        self.handshake_done = False

    def initialize(self, peer_kem_public, peer_sign_public):
        """
        Initialise le Triple Ratchet (premier échange) :
        - KEM pour secret partagé
        - Signature pour authentification
        """
        # Générer sa propre clé KEM si pas déjà fait
        if not self.DHs:
            self.DHs = self.kem.generate_keypair()
        self.DHr = peer_kem_public
        self.peer_sign_public_key = peer_sign_public
        # Échange initial (KEM encapsulation avec la clé publique du pair)
        ciphertext, shared_secret = self.kem.encapsulate(peer_kem_public)
        # Authentifier le message d'init (signature)
        signature = self.signature.sign(ciphertext, self.own_sign_keypair[1])
        # Initialiser la racine de clé
        self.root_key = self.kdf.derive_key(shared_secret, self.symmetric.key_size)
        self.send_chain_key = self.root_key
        self.recv_chain_key = self.root_key
        self.handshake_done = True
        return {
            'kem_ciphertext': ciphertext,
            'kem_signature': signature,
            'sign_public_key': self.own_sign_keypair[0]
        }

    def complete_handshake(self, kem_ciphertext, kem_signature, peer_sign_public):
        """
        Complète le Triple Ratchet côté répondeur :
        - Vérifie la signature
        - Décapsule le secret
        - Initialise la racine de clé
        """
        self.peer_sign_public_key = peer_sign_public
        # Vérifier la signature du peer
        if not self.signature.verify(kem_ciphertext, kem_signature, peer_sign_public):
            raise RuntimeError('Signature du peer invalide !')
        # Décapsuler le secret partagé avec notre clé privée
        # Le ciphertext a été encapsulé avec notre clé publique par Alice
        if not self.DHs:
            self.DHs = self.kem.generate_keypair()
        _, private_key = self.DHs
        shared_secret = self.kem.decapsulate(kem_ciphertext, private_key)
        # Initialiser les clés de chaîne avec le même secret partagé
        self.root_key = self.kdf.derive_key(shared_secret, self.symmetric.key_size)
        self.send_chain_key = self.root_key
        self.recv_chain_key = self.root_key
        self.handshake_done = True
        return True

    def ratchet_encrypt(self, plaintext, aad=None):
        """
        Chiffre un message avec rotation de clé (Double Ratchet + signature).
        Retourne ciphertext, nonce, signature, numéro de message.
        """
        if not self.handshake_done:
            raise RuntimeError('Ratchet non initialisé')
        
        # Utiliser la clé actuelle pour chiffrer
        key = self.send_chain_key
        ciphertext, nonce = self.symmetric.encrypt(plaintext, key, associated_data=aad)
        
        # Signature du message (authentification forte)
        signature = self.signature.sign(ciphertext, self.own_sign_keypair[1])
        msg_num = self.send_message_number
        
        # Rotation de la clé de chaîne d'envoi APRÈS le chiffrement
        self.send_chain_key = self.kdf.derive_key(self.send_chain_key, self.symmetric.key_size)
        self.send_message_number += 1
        
        return {
            'ciphertext': ciphertext,
            'nonce': nonce,
            'signature': signature,
            'msg_num': msg_num,
            'sign_public_key': self.own_sign_keypair[0]
        }

    def ratchet_decrypt(self, ciphertext, nonce, signature, msg_num, peer_sign_public, aad=None):
        """
        Déchiffre un message avec rotation de clé (Double Ratchet + vérification signature).
        """
        if not self.handshake_done:
            raise RuntimeError('Ratchet non initialisé')
        
        # Vérifier la signature
        if not self.signature.verify(ciphertext, signature, peer_sign_public):
            raise RuntimeError('Signature du message invalide !')
        
        # Utiliser la clé actuelle pour déchiffrer
        key = self.recv_chain_key
        plaintext = self.symmetric.decrypt(ciphertext, key, nonce, associated_data=aad)
        
        # Rotation de la clé de chaîne de réception APRÈS le déchiffrement
        self.recv_chain_key = self.kdf.derive_key(self.recv_chain_key, self.symmetric.key_size)
        self.recv_message_number += 1
        
        return plaintext

    def rekey(self):
        """
        Force le renouvellement des clés (rotation manuelle).
        """
        self.root_key = self.kdf.derive_key(self.root_key, self.symmetric.key_size)
        self.send_chain_key = self.root_key
        self.recv_chain_key = self.root_key
        return True 