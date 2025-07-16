#!/usr/bin/env python3
"""
Script de génération du diagramme de classes Kyberium
Génère un diagramme de classes professionnel au format PNG/SVG
"""

import subprocess
import sys
import os
from pathlib import Path

def check_plantuml():
    """Vérifie si PlantUML est installé"""
    try:
        result = subprocess.run(['plantuml', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PlantUML trouvé")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ PlantUML non trouvé")
    print("💡 Installation:")
    print("   - Java: sudo apt-get install default-jre")
    print("   - PlantUML: wget https://github.com/plantuml/plantuml/releases/download/v1.2023.10/plantuml-1.2023.10.jar")
    print("   - Alias: echo 'alias plantuml=\"java -jar plantuml.jar\"' >> ~/.bashrc")
    return False

def generate_diagram(input_file, output_format="png"):
    """Génère le diagramme à partir du fichier PlantUML"""
    if not os.path.exists(input_file):
        print(f"❌ Fichier d'entrée non trouvé: {input_file}")
        return False
    
    output_file = input_file.replace('.puml', f'.{output_format}')
    
    try:
        cmd = ['plantuml', f'-t{output_format}', input_file]
        print(f"🔄 Génération du diagramme: {cmd}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Diagramme généré: {output_file}")
            return True
        else:
            print(f"❌ Erreur lors de la génération:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Exception lors de la génération: {e}")
        return False

def generate_multiple_formats(input_file):
    """Génère le diagramme dans plusieurs formats"""
    formats = ["png", "svg", "pdf"]
    
    for fmt in formats:
        print(f"\n🔄 Génération au format {fmt.upper()}...")
        if generate_diagram(input_file, fmt):
            print(f"✅ Format {fmt.upper()} généré avec succès")
        else:
            print(f"❌ Échec de la génération au format {fmt.upper()}")

def main():
    """Fonction principale"""
    print("🚀 Générateur de diagramme de classes Kyberium")
    print("=" * 50)
    
    # Vérifier PlantUML
    if not check_plantuml():
        sys.exit(1)
    
    # Chemin du fichier PlantUML
    script_dir = Path(__file__).parent
    puml_file = script_dir / "class_diagram_kyberium.puml"
    
    if not puml_file.exists():
        print(f"❌ Fichier PlantUML non trouvé: {puml_file}")
        sys.exit(1)
    
    print(f"📁 Fichier source: {puml_file}")
    
    # Générer les diagrammes
    generate_multiple_formats(str(puml_file))
    
    print("\n🎉 Génération terminée!")
    print("📊 Formats disponibles:")
    for fmt in ["png", "svg", "pdf"]:
        output_file = puml_file.with_suffix(f'.{fmt}')
        if output_file.exists():
            size = output_file.stat().st_size
            print(f"   - {output_file.name} ({size} bytes)")

if __name__ == "__main__":
    main() 