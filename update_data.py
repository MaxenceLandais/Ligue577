import json
from datetime import datetime

# Ce script est exécuté par GitHub Actions (ou manuellement).
# Son rôle est de se connecter à une API (ex: Assemblée Nationale), 
# calculer les nouveaux scores, et mettre à jour data.json.

DATA_FILE = "data.json"

def calculate_band(score):
    if score >= 80: return "Libéral"
    if score >= 70: return "Plutôt libéral"
    if score >= 60: return "Modérément libéral"
    if score >= 50: return "Peu libéral"
    return "Dirigiste"

def update_database():
    print("🔄 Démarrage du Workflow de mise à jour...")
    
    # 1. Charger l'ancienne base de données
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # 2. ICI : Logique pour récupérer de nouvelles données
    # Exemple fictif : on simule l'ajout d'un point en fiscalité pour Gérault Verny
    # grace à un nouveau vote détecté.
    print("📡 Connexion aux Open Data de l'Assemblée (Simulation)...")
    
    for dep in data["deputies"]:
        # Simulation d'un algorithme d'IA/Scraping qui évalue les votes
        # ...
        
        # Recalculer le score total (sur 120 ramené à 100)
        total_points = sum(dep["scores_detail"].values())
        dep["score_total"] = round((total_points / 120) * 100, 1)
        
        # Mettre à jour la bande
        dep["bande"] = calculate_band(dep["score_total"])
        
    # 3. Mettre à jour la date de modification
    data["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 4. Sauvegarder
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Mise à jour terminée avec succès. Fichier {DATA_FILE} écrasé.")

if __name__ == "__main__":
    update_database()
