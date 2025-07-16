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

class SignatureInterface(ABC):
    @abstractmethod
    def generate_keypair(self):
        """Génère une paire de clés publique/privée pour la signature."""
        pass

    @abstractmethod
    def sign(self, message, private_key):
        """Signe un message avec la clé privée. Retourne la signature."""
        pass

    @abstractmethod
    def verify(self, message, signature, public_key):
        """Vérifie la signature d'un message avec la clé publique. Retourne True/False."""
        pass
