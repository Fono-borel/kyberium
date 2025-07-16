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

from .interface import SymmetricCipherInterface
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import os

class ChaCha20Cipher(SymmetricCipherInterface):
    """
    Implémentation du chiffrement symétrique ChaCha20-Poly1305 (AEAD).
    Fournit confidentialité et authenticité.
    """
    
    def __init__(self, key_size=32):
        """
        Initialise le module ChaCha20-Poly1305.
        Args:
            key_size (int): Taille de la clé en bytes (32 pour ChaCha20)
        """
        if key_size != 32:
            raise ValueError("ChaCha20-Poly1305 supporte uniquement 256 bits (32 bytes)")
        self.key_size = key_size
        self.nonce_size = 12  # 96 bits recommandé
    
    def encrypt(self, plaintext, key, nonce=None, associated_data=None):
        """
        Chiffre le message avec ChaCha20-Poly1305.
        Args:
            plaintext (bytes): Données à chiffrer
            key (bytes): Clé secrète
            nonce (bytes, optional): Nonce/IV (12 bytes recommandé)
            associated_data (bytes, optional): Données authentifiées mais non chiffrées (AAD)
        Returns:
            tuple: (ciphertext, nonce)
        """
        if not isinstance(plaintext, bytes):
            raise ValueError("Le plaintext doit être en bytes")
        if not isinstance(key, bytes) or len(key) != self.key_size:
            raise ValueError(f"La clé doit être en bytes de longueur {self.key_size}")
        if nonce is not None and (not isinstance(nonce, bytes) or len(nonce) != self.nonce_size):
            raise ValueError(f"Le nonce doit être en bytes de longueur {self.nonce_size}")
        if nonce is None:
            nonce = os.urandom(self.nonce_size)
        chacha = ChaCha20Poly1305(key)
        ciphertext = chacha.encrypt(nonce, plaintext, associated_data)
        return ciphertext, nonce
    
    def decrypt(self, ciphertext, key, nonce=None, associated_data=None):
        """
        Déchiffre le message avec ChaCha20-Poly1305.
        Args:
            ciphertext (bytes): Données chiffrées
            key (bytes): Clé secrète
            nonce (bytes): Nonce/IV utilisé lors du chiffrement
            associated_data (bytes, optional): Données authentifiées mais non chiffrées (AAD)
        Returns:
            bytes: Plaintext déchiffré
        """
        if not isinstance(ciphertext, bytes):
            raise ValueError("Le ciphertext doit être en bytes")
        if not isinstance(key, bytes) or len(key) != self.key_size:
            raise ValueError(f"La clé doit être en bytes de longueur {self.key_size}")
        if nonce is None or not isinstance(nonce, bytes) or len(nonce) != self.nonce_size:
            raise ValueError(f"Le nonce doit être en bytes de longueur {self.nonce_size}")
        chacha = ChaCha20Poly1305(key)
        try:
            plaintext = chacha.decrypt(nonce, ciphertext, associated_data)
            return plaintext
        except Exception as e:
            raise RuntimeError(f"Erreur de déchiffrement ou d'authentification ChaCha20-Poly1305: {e}")
