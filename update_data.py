import json
import os
from datetime import datetime

DATA_FILE = "data.json"

def calculate_scores(deputes):
    """Recalcule le score global et trie la liste des députés."""
    for d in deputes:
        scores = d.get("scores", {}).values()
        if scores:
            d["scoreGlobal"] = round(sum(scores) / len(scores))
        else:
            d["scoreGlobal"] = 0

    # Trier du meilleur au moins bon score
    deputes.sort(key=lambda x: x.get("scoreGlobal", 0), reverse=True)
    return deputes

def main():
    if not os.path.exists(DATA_FILE):
        print(f"❌ Erreur : {DATA_FILE} introuvable.")
        return

    print("🔄 Chargement de data.json...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        deputes = json.load(f)

    print(f"📊 Traitement de {len(deputes)} députés...")
    deputes_mis_a_jour = calculate_scores(deputes)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(deputes_mis_a_jour, f, ensure_ascii=False, indent=2)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"✅ Base de données mise à jour avec succès à {now} !")

if __name__ == "__main__":
    main()