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

import sys
import subprocess
import importlib.util
import os
from typing import Optional

def check_python_version() -> bool:
    """Vérifie que la version de Python est compatible (3.7+)"""
    if sys.version_info < (3, 7):
        print("❌ Kyberium nécessite Python 3.7 ou supérieur")
        return False
    return True

def check_and_install_dependency(module_name: str, pip_name: Optional[str] = None) -> bool:
    """
    Vérifie si un module est disponible, sinon tente de l'installer
    
    Args:
        module_name: Nom du module Python à importer
        pip_name: Nom du package pip (si différent du module_name)
    
    Returns:
        True si le module est disponible, False sinon
    """
    if pip_name is None:
        pip_name = module_name
    
    # Vérifier si le module est déjà disponible
    spec = importlib.util.find_spec(module_name)
    if spec is not None:
        return True
    
    print(f"📦 Module '{module_name}' non trouvé. Tentative d'installation...")
    
    try:
        # Vérifier que pip est disponible
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"❌ pip n'est pas disponible. Impossible d'installer {module_name}")
        return False
    
    try:
        # Installer le module
        print(f"🔧 Installation de {pip_name}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pip_name],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ {pip_name} installé avec succès")
        
        # Vérifier que l'installation a fonctionné
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            return True
        else:
            print(f"❌ Installation de {module_name} échouée")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation de {pip_name}: {e}")
        print(f"Sortie d'erreur: {e.stderr}")
        return False

def ensure_dependencies() -> bool:
    """
    Vérifie et installe automatiquement toutes les dépendances requises
    
    Returns:
        True si toutes les dépendances sont disponibles, False sinon
    """
    print("🔍 Vérification des dépendances Kyberium...")
    
    # Vérifier la version de Python
    if not check_python_version():
        return False
    
    # Liste des dépendances requises
    dependencies = [
        ("pqcrypto", "pqcrypto"),
        ("cryptography", "cryptography"),
    ]
    
    # Vérifier et installer chaque dépendance
    for module_name, pip_name in dependencies:
        if not check_and_install_dependency(module_name, pip_name):
            print(f"❌ Impossible de résoudre la dépendance: {module_name}")
            return False
    
    print("✅ Toutes les dépendances sont disponibles")
    return True

def safe_import(module_name: str, fallback_message: Optional[str] = None) -> Optional[object]:
    """
    Importe un module de manière sécurisée avec gestion d'erreur
    
    Args:
        module_name: Nom du module à importer
        fallback_message: Message à afficher en cas d'échec
    
    Returns:
        Le module importé ou None en cas d'échec
    """
    try:
        return __import__(module_name)
    except ImportError as e:
        if fallback_message:
            print(f"⚠️  {fallback_message}: {e}")
        else:
            print(f"⚠️  Impossible d'importer {module_name}: {e}")
        return None

# Vérifier les dépendances au démarrage
if not ensure_dependencies():
    print("❌ Kyberium ne peut pas démarrer - dépendances manquantes")
    print("💡 Essayez d'installer manuellement: pip install pqcrypto cryptography")
    sys.exit(1)

# Version de Kyberium
__version__ = "1.0.0"

# Informations sur le projet
__author__ = "Kyberium Team"
__description__ = "Librairie de chiffrement post-quantique modulaire"

print(f"🚀 Kyberium {__version__} initialisé avec succès")
