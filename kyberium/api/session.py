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
from kyberium.kdf.sha3 import SHA3KDF, SHAKE256KDF
from kyberium.signature.dilithium import DilithiumSignature
from kyberium.symmetric.aesgcm import AESGCMCipher
from kyberium.symmetric.chacha20 import ChaCha20Cipher
from kyberium.ratchet.triple_ratchet import TripleRatchet
import os

class SessionManager:
    """
    Gestionnaire de session cryptographique post-quantique, modulaire et robuste.
    Permet de choisir dynamiquement les modules KEM, KDF, Signature, Symmetric.
    Gère le handshake, la session, la rotation des clés, et l'orchestration des primitives.
    Peut utiliser le Triple Ratchet pour la PFS avancée.
    """
    def __init__(self,
                 kem=None,
                 kdf=None,
                 signature=None,
                 symmetric=None,
                 symmetric_key_size=32,
                 kdf_type='sha3',
                 symmetric_type='aesgcm',
                 use_triple_ratchet=False):
        # Modules par défaut
        self.kem = kem or Kyber1024()
        if kdf_type == 'sha3':
            self.kdf = kdf or SHA3KDF()
        elif kdf_type == 'shake256':
            self.kdf = kdf or SHAKE256KDF()
        else:
            raise ValueError('Type de KDF inconnu')
        self.signature = signature or DilithiumSignature()
        if symmetric_type == 'aesgcm':
            self.symmetric = symmetric or AESGCMCipher(key_size=symmetric_key_size)
        elif symmetric_type == 'chacha20':
            self.symmetric = symmetric or ChaCha20Cipher(key_size=symmetric_key_size)
        else:
            raise ValueError('Type de chiffrement symétrique inconnu')
        self.session_keys = {}
        self.handshake_done = False
        self.peer_public_key = None
        self.own_keypair = None
        self.shared_secret = None
        self.session_id = None
        # Triple Ratchet
        self.use_triple_ratchet = use_triple_ratchet
        self.triple_ratchet = None
        # Clés de signature séparées
        self.own_sign_keypair = self.signature.generate_keypair()
        self.peer_sign_public_key = None

    def generate_kem_keypair(self):
        """Génère une paire de clés KEM pour l'échange de session."""
        self.own_keypair = self.kem.generate_keypair()
        return self.own_keypair

    def get_public_key(self):
        """Retourne la clé publique KEM locale."""
        if not self.own_keypair:
            self.generate_kem_keypair()
        return self.own_keypair[0]

    def get_sign_public_key(self):
        """Retourne la clé publique de signature locale."""
        return self.own_sign_keypair[0]

    def set_peer_public_key(self, peer_public_key):
        """Enregistre la clé publique KEM du pair."""
        self.peer_public_key = peer_public_key

    def set_peer_sign_public_key(self, peer_sign_public_key):
        """Enregistre la clé publique de signature du pair."""
        self.peer_sign_public_key = peer_sign_public_key

    def handshake_initiator(self):
        """
        Effectue le handshake côté initiateur (client) :
        - encapsule un secret avec la clé publique du pair
        - dérive la clé de session
        """
        if not self.peer_public_key:
            raise ValueError('Clé publique du pair non définie')
        ciphertext, shared_secret = self.kem.encapsulate(self.peer_public_key)
        self.shared_secret = shared_secret
        self.session_id = os.urandom(16)
        self.session_keys['encryption'] = self.kdf.derive_key(shared_secret, self.symmetric.key_size)
        self.handshake_done = True
        return ciphertext

    def handshake_responder(self, ciphertext):
        """
        Effectue le handshake côté répondeur (serveur) :
        - décapsule le secret avec la clé privée locale
        - dérive la clé de session
        """
        if not self.own_keypair:
            raise ValueError('Paire de clés KEM non générée')
        _, private_key = self.own_keypair
        shared_secret = self.kem.decapsulate(ciphertext, private_key)
        self.shared_secret = shared_secret
        self.session_id = os.urandom(16)
        self.session_keys['encryption'] = self.kdf.derive_key(shared_secret, self.symmetric.key_size)
        self.handshake_done = True
        return True

    def encrypt(self, plaintext, aad=None):
        """
        Chiffre un message avec la clé de session.
        Args:
            plaintext (bytes): Données à chiffrer
            aad (bytes, optional): Données authentifiées
        Returns:
            tuple: (ciphertext, nonce)
        """
        if not self.handshake_done:
            raise RuntimeError('Session non initialisée')
        key = self.session_keys['encryption']
        return self.symmetric.encrypt(plaintext, key, associated_data=aad)

    def decrypt(self, ciphertext, nonce, aad=None):
        """
        Déchiffre un message avec la clé de session.
        Args:
            ciphertext (bytes): Données chiffrées
            nonce (bytes): Nonce utilisé lors du chiffrement
            aad (bytes, optional): Données authentifiées
        Returns:
            bytes: Plaintext déchiffré
        """
        if not self.handshake_done:
            raise RuntimeError('Session non initialisée')
        key = self.session_keys['encryption']
        return self.symmetric.decrypt(ciphertext, key, nonce, associated_data=aad)

    def sign(self, message):
        """
        Signe un message avec la clé privée de signature dédiée.
        """
        return self.signature.sign(message, self.own_sign_keypair[1])

    def verify(self, message, signature, public_key=None):
        """
        Vérifie la signature d'un message avec la clé publique de signature.
        Args:
            message (bytes): Message original
            signature (bytes): Signature à vérifier
            public_key (bytes, optional): Clé publique de vérification (par défaut celle du pair)
        Returns:
            bool: True si la signature est valide
        """
        if public_key is None:
            public_key = self.peer_sign_public_key
        return self.signature.verify(message, signature, public_key)

    def rotate_session_key(self):
        """
        Renouvelle la clé de session (PFS, à intégrer avec Double Ratchet plus tard).
        """
        if not self.shared_secret:
            raise RuntimeError('Aucun secret partagé pour la rotation')
        new_secret = os.urandom(len(self.shared_secret))
        self.session_keys['encryption'] = self.kdf.derive_key(new_secret, self.symmetric.key_size)
        return True

    # --- Triple Ratchet ---
    def triple_ratchet_init(self, peer_kem_public, peer_sign_public):
        """
        Initialise le Triple Ratchet (côté initiateur).
        Retourne le message d'init à transmettre au pair.
        """
        self.triple_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=self.own_keypair  # Injection de la paire de clés KEM
        )
        return self.triple_ratchet.initialize(peer_kem_public, peer_sign_public)

    def triple_ratchet_complete_handshake(self, kem_ciphertext, kem_signature, peer_sign_public):
        """
        Complète le Triple Ratchet (côté répondeur).
        """
        self.triple_ratchet = TripleRatchet(
            kem=self.kem,
            kdf=self.kdf,
            signature=self.signature,
            symmetric=self.symmetric,
            own_kem_keypair=self.own_keypair  # Injection de la paire de clés KEM
        )
        return self.triple_ratchet.complete_handshake(kem_ciphertext, kem_signature, peer_sign_public)

    def triple_ratchet_encrypt(self, plaintext, aad=None):
        """
        Chiffre un message avec Triple Ratchet (rotation + signature).
        Retourne un dict avec ciphertext, nonce, signature, msg_num, sign_public_key.
        """
        if not self.triple_ratchet:
            raise RuntimeError('Triple Ratchet non initialisé')
        return self.triple_ratchet.ratchet_encrypt(plaintext, aad)

    def triple_ratchet_decrypt(self, ciphertext, nonce, signature, msg_num, peer_sign_public, aad=None):
        """
        Déchiffre un message avec Triple Ratchet (rotation + vérification signature).
        """
        if not self.triple_ratchet:
            raise RuntimeError('Triple Ratchet non initialisé')
        return self.triple_ratchet.ratchet_decrypt(ciphertext, nonce, signature, msg_num, peer_sign_public, aad)
