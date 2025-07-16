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

# Sous-package utilitaires de Kyberium

"""
Utilitaires et fonctions d'aide pour Kyberium.

Ce module contient des fonctions utilitaires, des exceptions personnalisées
et des helpers pour faciliter l'utilisation de Kyberium.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import des exceptions personnalisées
try:
    from .exceptions import *
except ImportError:
    # Si le fichier exceptions.py n'existe pas encore, on définit les exceptions de base
    pass

# Import des fonctions utilitaires
try:
    from .helpers import *
except ImportError:
    # Si le fichier helpers.py n'existe pas encore, on définit les helpers de base
    pass

# Version du module
__version__ = "1.0.0"

# Informations sur le module
__author__ = "Kyberium Team"
__description__ = "Utilitaires et fonctions d'aide pour Kyberium" 