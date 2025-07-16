#!/usr/bin/env python3
"""
Script d'organisation des tests Kyberium
Organise automatiquement tous les fichiers de test dans la structure appropriée
"""

import os
import shutil
import glob
from pathlib import Path

def create_test_structure():
    """Crée la structure de tests organisée"""
    
    # Structure des tests
    test_structure = {
        'tests/unit/': [
            'test_kem.py',
            'test_signature.py', 
            'test_symmetric.py',
            'test_kdf.py',
            'test_ratchet.py',
            'test_protocol.py'
        ],
        'tests/integration/': [
            'test_api.py',
            'test_integration_python.py',
            'test_simple_integration.py',
            'test_interoperability.py'
        ],
        'tests/security/': [
            'test_triple_ratchet_api.py',
            'test_triple_ratchet_comprehensive.py',
            'test_triple_ratchet_debug.py',
            'test_triple_ratchet.py'
        ],
        'tests/messenger/': [
            'test_gui_fix.py',
            'test_integration.py',
            'test_kyberium_simple.py',
            'test_multi_users.py',
            'test_private_messages.py',
            'test_triple_ratchet.py'
        ],
        'tests/performance/': [
            'test_benchmarks.py'
        ]
    }
    
    # Créer les répertoires
    for directory in test_structure.keys():
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Répertoire créé : {directory}")
    
    return test_structure

def find_and_move_tests():
    """Trouve et déplace les fichiers de test"""
    
    # Chercher tous les fichiers de test
    test_files = []
    
    # Chercher dans le répertoire racine
    for file in glob.glob("test_*.py"):
        test_files.append(file)
    
    # Chercher dans messenger_app
    for file in glob.glob("messenger_app/test_*.py"):
        test_files.append(file)
    
    # Chercher dans examples
    for file in glob.glob("examples/test_*.py"):
        test_files.append(file)
    
    print(f"📁 Fichiers de test trouvés : {len(test_files)}")
    
    # Déplacer les fichiers selon leur type
    for file in test_files:
        source_path = Path(file)
        
        if not source_path.exists():
            continue
            
        # Déterminer la destination selon le nom du fichier
        if 'kem' in file.lower():
            dest_dir = 'tests/unit/'
        elif 'signature' in file.lower():
            dest_dir = 'tests/unit/'
        elif 'symmetric' in file.lower():
            dest_dir = 'tests/unit/'
        elif 'kdf' in file.lower():
            dest_dir = 'tests/unit/'
        elif 'ratchet' in file.lower():
            if 'comprehensive' in file.lower() or 'api' in file.lower():
                dest_dir = 'tests/security/'
            else:
                dest_dir = 'tests/unit/'
        elif 'api' in file.lower():
            dest_dir = 'tests/integration/'
        elif 'integration' in file.lower():
            dest_dir = 'tests/integration/'
        elif 'gui' in file.lower() or 'messenger' in file.lower():
            dest_dir = 'tests/messenger/'
        elif 'performance' in file.lower() or 'benchmark' in file.lower():
            dest_dir = 'tests/performance/'
        elif 'security' in file.lower():
            dest_dir = 'tests/security/'
        else:
            dest_dir = 'tests/unit/'
        
        # Déplacer le fichier
        dest_path = Path(dest_dir) / source_path.name
        
        if dest_path.exists():
            print(f"⚠️  Fichier existe déjà : {dest_path}")
            continue
            
        try:
            shutil.move(str(source_path), str(dest_path))
            print(f"✅ Déplacé : {source_path} → {dest_path}")
        except Exception as e:
            print(f"❌ Erreur lors du déplacement de {source_path}: {e}")

def create_init_files():
    """Crée les fichiers __init__.py dans les répertoires de tests"""
    
    test_dirs = [
        'tests/',
        'tests/unit/',
        'tests/integration/',
        'tests/security/',
        'tests/messenger/',
        'tests/performance/'
    ]
    
    for directory in test_dirs:
        init_file = Path(directory) / '__init__.py'
        if not init_file.exists():
            init_file.touch()
            print(f"✅ Fichier __init__.py créé : {init_file}")

def create_test_config():
    """Crée la configuration de tests"""
    
    # pytest.ini
    pytest_config = """[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    unit: Tests unitaires
    integration: Tests d'intégration
    security: Tests de sécurité
    performance: Tests de performance
    slow: Tests lents
    gui: Tests interface graphique
"""
    
    with open('pytest.ini', 'w') as f:
        f.write(pytest_config)
    print("✅ Configuration pytest.ini créée")
    
    # tox.ini
    tox_config = """[tox]
envlist = py38, py39, py310, py311

[testenv]
deps =
    pytest>=7.0.0
    pytest-cov>=4.0.0
    pytest-xdist>=3.0.0
    pytest-mock>=3.10.0
commands =
    pytest tests/ -v --cov=kyberium --cov-report=html
"""
    
    with open('tox.ini', 'w') as f:
        f.write(tox_config)
    print("✅ Configuration tox.ini créée")

def create_test_runner():
    """Crée un script de lancement des tests"""
    
    runner_script = """#!/usr/bin/env python3
\"\"\"
Script de lancement des tests Kyberium
\"\"\"

import subprocess
import sys
import argparse

def run_tests(test_type, verbose=False, coverage=False):
    \"\"\"Lance les tests selon le type spécifié\"\"\"
    
    cmd = ['python', '-m', 'pytest']
    
    if test_type == 'all':
        cmd.append('tests/')
    elif test_type == 'unit':
        cmd.append('tests/unit/')
    elif test_type == 'integration':
        cmd.append('tests/integration/')
    elif test_type == 'security':
        cmd.append('tests/security/')
    elif test_type == 'messenger':
        cmd.append('tests/messenger/')
    elif test_type == 'performance':
        cmd.append('tests/performance/')
    else:
        print(f"❌ Type de test inconnu : {test_type}")
        return False
    
    if verbose:
        cmd.append('-v')
    
    if coverage:
        cmd.extend(['--cov=kyberium', '--cov-report=html'])
    
    print(f"🚀 Lancement des tests : {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ Tests terminés avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'exécution des tests : {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Lanceur de tests Kyberium')
    parser.add_argument('type', choices=['all', 'unit', 'integration', 'security', 'messenger', 'performance'],
                       help='Type de tests à exécuter')
    parser.add_argument('-v', '--verbose', action='store_true', help='Mode verbeux')
    parser.add_argument('-c', '--coverage', action='store_true', help='Générer un rapport de couverture')
    
    args = parser.parse_args()
    
    success = run_tests(args.type, args.verbose, args.coverage)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
"""
    
    with open('run_tests.py', 'w') as f:
        f.write(runner_script)
    
    # Rendre le script exécutable
    os.chmod('run_tests.py', 0o755)
    print("✅ Script de lancement des tests créé : run_tests.py")

def main():
    """Fonction principale"""
    print("🔧 Organisation des tests Kyberium")
    print("=" * 50)
    
    # Créer la structure
    print("\n📁 Création de la structure de tests...")
    create_test_structure()
    
    # Déplacer les fichiers
    print("\n📦 Déplacement des fichiers de test...")
    find_and_move_tests()
    
    # Créer les fichiers __init__.py
    print("\n📄 Création des fichiers __init__.py...")
    create_init_files()
    
    # Créer la configuration
    print("\n⚙️  Création de la configuration...")
    create_test_config()
    
    # Créer le script de lancement
    print("\n🚀 Création du script de lancement...")
    create_test_runner()
    
    print("\n🎉 Organisation terminée !")
    print("\n📋 Utilisation :")
    print("  python run_tests.py all          # Tous les tests")
    print("  python run_tests.py unit         # Tests unitaires")
    print("  python run_tests.py security     # Tests de sécurité")
    print("  python run_tests.py performance  # Tests de performance")
    print("  python run_tests.py all -c       # Avec couverture")

if __name__ == '__main__':
    main() 