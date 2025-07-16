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

class DoubleRatchetInterface(ABC):
    @abstractmethod
    def initialize(self, shared_secret, root_key=None):
        """Initialise le ratchet avec le secret partagé et éventuellement une racine de clé."""
        pass

    @abstractmethod
    def ratchet_encrypt(self, plaintext):
        """Chiffre un message en avançant le ratchet. Retourne le ciphertext et les métadonnées nécessaires."""
        pass

    @abstractmethod
    def ratchet_decrypt(self, ciphertext, metadata):
        """Déchiffre un message en avançant le ratchet avec les métadonnées reçues."""
        pass

    @abstractmethod
    def rekey(self):
        """Force le renouvellement des clés (par exemple, après un certain nombre de messages)."""
        pass
