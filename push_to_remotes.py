import subprocess

# Configuration des remotes
remotes = {
    "origin": "https://gitlab.com/fonoborel-group/kyberium.git",
    "github": "https://github.com/Fono-borel/kyberium.git"
}

def run_command(command, description):
    print(f"🔹 {description}...")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ OK")
    else:
        print("❌ Erreur")
        print(result.stderr)
    return result.returncode == 0

def set_remotes():
    run_command(["git", "remote", "remove", "origin"], "Suppression ancienne remote origin")
    run_command(["git", "remote", "add", "origin", remotes["origin"]], "Ajout remote GitLab (origin)")
    run_command(["git", "remote", "add", "github", remotes["github"]], "Ajout remote GitHub")

def sync_and_push(branch="main"):
    print(f"\n🔄 Synchronisation avec GitLab (origin/{branch})")
    if run_command(["git", "pull", "origin", branch], f"Pull depuis GitLab ({branch})"):
        print(f"\n🚀 Poussée vers tous les dépôts (branche {branch})")
        for name in remotes:
            run_command(["git", "push", name, branch], f"Push vers {name}")

if __name__ == "__main__":
    set_remotes()
    sync_and_push()