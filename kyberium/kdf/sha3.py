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

# Kyberium - Cryptographie Post-Quantique
# Copyright (C) 2025 RhaB17369
# Licence : GNU GPL v3
# Voir le fichier LICENSE pour plus de détails

from .interface import KDFInterface
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import os

class SHA3KDF(KDFInterface):
    """
    Implémentation de KDF basée sur SHA-3 utilisant HKDF (HMAC-based Key Derivation Function).
    
    HKDF est un standard RFC 5869 qui utilise HMAC pour dériver des clés de manière sécurisée.
    Cette implémentation utilise SHA-3-256 comme fonction de hachage sous-jacente.
    """
    
    def __init__(self, hash_algorithm=None):
        """
        Initialise le KDF SHA-3.
        
        Args:
            hash_algorithm: Algorithme de hachage à utiliser (par défaut SHA3-256)
        """
        self.hash_algorithm = hash_algorithm or hashes.SHA3_256()
    
    def derive_key(self, input_key_material, length, salt=None, info=None):
        """
        Dérive une clé de la longueur spécifiée à partir du matériel d'entrée.
        
        Args:
            input_key_material (bytes): Le matériel d'entrée (ex: secret partagé)
            length (int): Longueur de la clé à dériver en bytes
            salt (bytes, optional): Sel pour la dérivation (recommandé pour la sécurité)
            info (bytes, optional): Contexte d'application (ex: "session_key", "auth_key")
            
        Returns:
            bytes: La clé dérivée
            
        Raises:
            ValueError: Si les paramètres sont invalides
            RuntimeError: Si la dérivation échoue
        """
        try:
            if not isinstance(input_key_material, bytes):
                raise ValueError("Le matériel d'entrée doit être en bytes")
            
            if not isinstance(length, int) or length <= 0:
                raise ValueError("La longueur doit être un entier positif")
            
            if salt is not None and not isinstance(salt, bytes):
                raise ValueError("Le sel doit être en bytes")
            
            if info is not None and not isinstance(info, bytes):
                raise ValueError("L'info doit être en bytes")
            
            # Utiliser un sel par défaut si aucun n'est fourni
            if salt is None:
                salt = b'kyberium_default_salt'
            
            # Utiliser une info par défaut si aucune n'est fournie
            if info is None:
                info = b'kyberium_default_info'
            
            # Créer l'instance HKDF
            hkdf = HKDF(
                algorithm=self.hash_algorithm,
                length=length,
                salt=salt,
                info=info,
            )
            
            # Dériver la clé
            derived_key = hkdf.derive(input_key_material)
            
            return derived_key
            
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la dérivation de clé: {e}")
    
    def get_algorithm_info(self):
        """
        Retourne les informations sur l'algorithme KDF.
        
        Returns:
            dict: Informations sur l'algorithme
        """
        return {
            "name": "HKDF-SHA3-256",
            "hash_algorithm": "SHA3-256",
            "standard": "RFC 5869",
            "security_level": "256 bits",
            "quantum_resistant": False,  # SHA-3 n'est pas post-quantique
            "recommended": True
        }


class SHAKE256KDF(KDFInterface):
    """
    Implémentation de KDF basée sur SHAKE-256 (SHA-3 extensible).
    
    SHAKE-256 est une fonction de hachage extensible qui peut produire une sortie
    de n'importe quelle longueur, ce qui la rend idéale pour la dérivation de clés.
    """
    
    def __init__(self, digest_size=32):
        """
        Initialise le KDF SHAKE-256.
        
        Args:
            digest_size (int): Taille de sortie par défaut en bytes (32 = 256 bits)
        """
        self.digest_size = digest_size
        self.hash_algorithm = hashes.SHAKE256(digest_size)
    
    def derive_key(self, input_key_material, length, salt=None, info=None):
        """
        Dérive une clé de la longueur spécifiée à partir du matériel d'entrée.
        
        Args:
            input_key_material (bytes): Le matériel d'entrée (ex: secret partagé)
            length (int): Longueur de la clé à dériver en bytes
            salt (bytes, optional): Sel pour la dérivation
            info (bytes, optional): Contexte d'application
            
        Returns:
            bytes: La clé dérivée
            
        Raises:
            ValueError: Si les paramètres sont invalides
            RuntimeError: Si la dérivation échoue
        """
        try:
            if not isinstance(input_key_material, bytes):
                raise ValueError("Le matériel d'entrée doit être en bytes")
            
            if not isinstance(length, int) or length <= 0:
                raise ValueError("La longueur doit être un entier positif")
            
            if salt is not None and not isinstance(salt, bytes):
                raise ValueError("Le sel doit être en bytes")
            
            if info is not None and not isinstance(info, bytes):
                raise ValueError("L'info doit être en bytes")
            
            # Préparer le matériel d'entrée avec sel et info
            material = input_key_material
            
            if salt:
                material = salt + material
            
            if info:
                material = material + info
            
            # Utiliser SHAKE-256 pour dériver la clé
            h = hashes.Hash(hashes.SHAKE256(length))
            h.update(material)
            derived_key = h.finalize()
            
            return derived_key
            
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la dérivation de clé SHAKE-256: {e}")
    
    def get_algorithm_info(self):
        """
        Retourne les informations sur l'algorithme KDF.
        
        Returns:
            dict: Informations sur l'algorithme
        """
        return {
            "name": "SHAKE-256-KDF",
            "hash_algorithm": "SHAKE-256",
            "standard": "FIPS 202",
            "security_level": "256 bits",
            "quantum_resistant": False,  # SHAKE-256 n'est pas post-quantique
            "extensible": True,
            "recommended": True
        }
