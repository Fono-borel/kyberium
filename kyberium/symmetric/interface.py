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

from abc import ABC, abstractmethod

class SymmetricCipherInterface(ABC):
    @abstractmethod
    def encrypt(self, plaintext, key, nonce=None, associated_data=None):
        """Chiffre le message avec la clé et retourne le ciphertext (et éventuellement le tag d'authentification)."""
        pass

    @abstractmethod
    def decrypt(self, ciphertext, key, nonce=None, associated_data=None):
        """Déchiffre le ciphertext avec la clé et retourne le plaintext (ou lève une exception si l'authentification échoue)."""
        pass
