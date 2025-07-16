#!/usr/bin/env python3
"""
Script de lancement des tests Kyberium
"""

import subprocess
import sys
import argparse

def run_tests(test_type, verbose=False, coverage=False):
    """Lance les tests selon le type spécifié"""
    
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
