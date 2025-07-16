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

from .interface import SignatureInterface
from pqcrypto.sign import ml_dsa_65
import os

class DilithiumSignature(SignatureInterface):
    """
    Implémentation de CRYSTALS-Dilithium (ML-DSA-65) pour la signature post-quantique.
    
    Dilithium est l'un des algorithmes de signature post-quantique standardisés par NIST
    pour la sécurité de niveau 5 (équivalent à AES-256) contre les attaques classiques et quantiques.
    """
    
    def __init__(self):
        """Initialise le module Dilithium."""
        self.signature = ml_dsa_65
    
    def generate_keypair(self):
        """
        Génère une paire de clés publique/privée Dilithium.
        
        Returns:
            tuple: (public_key, private_key) en bytes
        """
        try:
            public_key, private_key = self.signature.generate_keypair()
            return public_key, private_key
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la génération de clés Dilithium: {e}")
    
    def sign(self, message, private_key):
        """
        Signe un message avec la clé privée.
        
        Args:
            message (bytes): Message à signer
            private_key (bytes): Clé privée
            
        Returns:
            bytes: Signature du message
            
        Raises:
            ValueError: Si les paramètres sont invalides
            RuntimeError: Si la signature échoue
        """
        try:
            if not isinstance(message, bytes):
                raise ValueError("Le message doit être en bytes")
            
            if not isinstance(private_key, bytes):
                raise ValueError("La clé privée doit être en bytes")
            
            if len(private_key) != self.signature.SECRET_KEY_SIZE:
                raise ValueError(f"Taille de clé privée invalide. Attendu: {self.signature.SECRET_KEY_SIZE}, Reçu: {len(private_key)}")
            
            signature = self.signature.sign(private_key, message)
            return signature
            
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la signature Dilithium: {e}")
    
    def verify(self, message, signature, public_key):
        """
        Vérifie la signature d'un message avec la clé publique.
        
        Args:
            message (bytes): Message original
            signature (bytes): Signature à vérifier
            public_key (bytes): Clé publique
            
        Returns:
            bool: True si la signature est valide, False sinon
            
        Raises:
            ValueError: Si les paramètres sont invalides
            RuntimeError: Si la vérification échoue
        """
        try:
            if not isinstance(message, bytes):
                raise ValueError("Le message doit être en bytes")
            
            if not isinstance(signature, bytes):
                raise ValueError("La signature doit être en bytes")
            
            if not isinstance(public_key, bytes):
                raise ValueError("La clé publique doit être en bytes")
            
            if len(public_key) != self.signature.PUBLIC_KEY_SIZE:
                raise ValueError(f"Taille de clé publique invalide. Attendu: {self.signature.PUBLIC_KEY_SIZE}, Reçu: {len(public_key)}")
            
            if len(signature) != self.signature.SIGNATURE_SIZE:
                raise ValueError(f"Taille de signature invalide. Attendu: {self.signature.SIGNATURE_SIZE}, Reçu: {len(signature)}")
            
            is_valid = self.signature.verify(public_key, message, signature)
            return is_valid
            
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la vérification Dilithium: {e}")
    
    def get_algorithm_info(self):
        """
        Retourne les informations sur l'algorithme Dilithium.
        
        Returns:
            dict: Informations sur l'algorithme
        """
        return {
            "name": "CRYSTALS-Dilithium (ML-DSA-65)",
            "security_level": 5,  # NIST Level 5
            "public_key_size": self.signature.PUBLIC_KEY_SIZE,
            "private_key_size": self.signature.SECRET_KEY_SIZE,
            "signature_size": self.signature.SIGNATURE_SIZE,
            "quantum_resistant": True,
            "standardized": True,
            "standard": "NIST PQC"
        }


# Garder l'ancienne classe pour la compatibilité (à supprimer plus tard)
class DummyDilithium(SignatureInterface):
    def generate_keypair(self):
        # Retourne une fausse paire de clés (clé publique, clé privée)
        return b'public_key', b'private_key'

    def sign(self, message, private_key):
        # Retourne une fausse signature
        return b'signature'

    def verify(self, message, signature, public_key):
        # Vérifie la fausse signature (toujours True pour le dummy)
        return signature == b'signature'
