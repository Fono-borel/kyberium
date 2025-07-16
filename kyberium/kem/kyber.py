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

from .interface import KEMInterface
from pqcrypto.kem import ml_kem_1024
import os

class Kyber1024(KEMInterface):
    """
    Implémentation de CRYSTALS-Kyber-1024 (ML-KEM-1024) pour l'échange de clés post-quantique.
    
    Kyber-1024 est l'une des variantes standardisées par NIST pour la sécurité
    de niveau 5 (équivalent à AES-256) contre les attaques classiques et quantiques.
    """
    
    def __init__(self):
        """Initialise le module Kyber-1024."""
        self.kem = ml_kem_1024
    
    def generate_keypair(self):
        """
        Génère une paire de clés publique/privée Kyber-1024.
        
        Returns:
            tuple: (public_key, private_key) en bytes
        """
        try:
            public_key, private_key = self.kem.generate_keypair()
            return public_key, private_key
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la génération de clés Kyber: {e}")
    
    def encapsulate(self, public_key):
        """
        Encapsule une clé de session avec la clé publique du destinataire.
        
        Args:
            public_key (bytes): Clé publique du destinataire
            
        Returns:
            tuple: (ciphertext, shared_secret) en bytes
            
        Raises:
            ValueError: Si la clé publique est invalide
            RuntimeError: Si l'encapsulation échoue
        """
        try:
            if not isinstance(public_key, bytes):
                raise ValueError("La clé publique doit être en bytes")
            
            if len(public_key) != self.kem.PUBLIC_KEY_SIZE:
                raise ValueError(f"Taille de clé publique invalide. Attendu: {self.kem.PUBLIC_KEY_SIZE}, Reçu: {len(public_key)})")
            
            ciphertext, shared_secret = self.kem.encrypt(public_key)
            # Vérification post-encapsulation
            if not isinstance(ciphertext, bytes) or len(ciphertext) != self.kem.CIPHERTEXT_SIZE:
                raise RuntimeError("Ciphertext généré invalide (corruption possible)")
            if not isinstance(shared_secret, bytes) or len(shared_secret) != self.kem.PLAINTEXT_SIZE:
                raise RuntimeError("Secret partagé généré invalide (corruption possible)")
            return ciphertext, shared_secret
            
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'encapsulation Kyber: {e}")
    
    def decapsulate(self, ciphertext, private_key):
        """
        Décapsule le ciphertext avec la clé privée pour retrouver le secret partagé.
        
        Args:
            ciphertext (bytes): Ciphertext à décapsuler
            private_key (bytes): Clé privée du destinataire
            
        Returns:
            bytes: Le secret partagé
            
        Raises:
            ValueError: Si les paramètres sont invalides
            RuntimeError: Si la décapsulation échoue
        """
        try:
            if not isinstance(ciphertext, bytes):
                raise ValueError("Le ciphertext doit être en bytes")
            
            if not isinstance(private_key, bytes):
                raise ValueError("La clé privée doit être en bytes")
            
            if len(private_key) != self.kem.SECRET_KEY_SIZE:
                raise ValueError(f"Taille de clé privée invalide. Attendu: {self.kem.SECRET_KEY_SIZE}, Reçu: {len(private_key)})")
            
            if len(ciphertext) != self.kem.CIPHERTEXT_SIZE:
                raise ValueError(f"Taille de ciphertext invalide. Attendu: {self.kem.CIPHERTEXT_SIZE}, Reçu: {len(ciphertext)})")
            
            shared_secret = self.kem.decrypt(private_key, ciphertext)
            # Vérification post-décapsulation
            if not isinstance(shared_secret, bytes) or len(shared_secret) != self.kem.PLAINTEXT_SIZE:
                raise RuntimeError("Secret partagé décapsulé invalide (corruption possible)")
            return shared_secret
            
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la décapsulation Kyber: {e}")
    
    def get_algorithm_info(self):
        """
        Retourne les informations sur l'algorithme Kyber-1024.
        
        Returns:
            dict: Informations sur l'algorithme
        """
        return {
            "name": "CRYSTALS-Kyber-1024 (ML-KEM-1024)",
            "security_level": 5,  # NIST Level 5
            "public_key_size": self.kem.PUBLIC_KEY_SIZE,
            "private_key_size": self.kem.SECRET_KEY_SIZE,
            "ciphertext_size": self.kem.CIPHERTEXT_SIZE,
            "shared_secret_size": self.kem.PLAINTEXT_SIZE,
            "quantum_resistant": True,
            "standardized": True,
            "standard": "NIST PQC"
        }


# Garder l'ancienne classe pour la compatibilité (à supprimer plus tard)
class DummyKyber(KEMInterface):
    def generate_keypair(self):
        # Retourne une fausse paire de clés (clé publique, clé privée)
        return b'public_key', b'private_key'

    def encapsulate(self, public_key):
        # Retourne un faux ciphertext et un faux secret partagé
        return b'ciphertext', b'shared_secret'

    def decapsulate(self, ciphertext, private_key):
        # Retourne un faux secret partagé
        return b'shared_secret'
