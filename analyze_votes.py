import json
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Charge les variables d'environnement définies dans le fichier .env
load_dotenv()


def analyze_all_udr_votes():
    # 1. Chargement des bases de données
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            deputes_db = json.load(f)
    except FileNotFoundError:
        print("❌ Erreur : 'data.json' est introuvable.")
        return

    try:
        with open("votes.json", "r", encoding="utf-8") as f:
            all_votes = json.load(f)
    except FileNotFoundError:
        print("❌ Erreur : 'votes.json' est introuvable. Exécutez d'abord scrape_votes.py.")
        return

    # Filtrer uniquement les députés appartenants au groupe UDR
    udr_deputes = [d for d in deputes_db if d.get("groupe", "").upper() == "UDR"]
    total_deputes = len(udr_deputes)

    if total_deputes == 0:
        print("⚠️ Aucun député UDR trouvé dans data.json.")
        return

    # 2. Préparation du client Gemini (initialisé une seule fois)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ GEMINI_API_KEY non trouvée dans le fichier .env")
        api_key = input("Entrez votre clé API Gemini : ").strip()

    client = genai.Client(api_key=api_key)

    print(f"🚀 Début de l'analyse Gemini en lot pour {total_deputes} députés UDR...\n" + "─" * 60)

    # 3. Traitement avec indicateurs de progression
    for index, depute in enumerate(udr_deputes, start=1):
        depute_id = depute.get("id")
        nom = depute.get("nom", depute_id)
        percent = int((index / total_deputes) * 100)

        # Marqueur de progression clair dans le terminal
        progress_bar = "█" * (percent // 5) + "░" * (20 - (percent // 5))
        print(f"[{index}/{total_deputes} | {percent:3d}%] [{progress_bar}] 🤖 Analyse : {nom} ({depute_id})")

        votes = all_votes.get(depute_id, [])
        if not votes:
            print(f"  ⏩ Aucun vote trouvé dans votes.json pour {nom}. Ignoré.\n")
            continue

        prompt = f"""
        Tu es un analyste en économie libérale. Analyse les votes du député ci-dessous et évalue son positionnement sur les 6 piliers économiques (notes de 0 à 100, 50 étant neutre) :
        - FIS (Santé Fiscale & Impôts) : Baisse des impôts, attractivité.
        - ETA (Taille de l'État & Dépenses) : Réduction de la dépense publique et des déficits.
        - REG (Fardeau Réglementaire) : Dérégulation, simplification administrative.
        - PRO (Droit de Propriété) : Protection de la propriété privée et du capital.
        - LIB (Liberté du Travail) : Flexibilité du travail, liberté d'embauche.
        - OUV (Ouverture des Marchés) : Concurrence, libre-échange, déblocage des marchés.

        Votes du député :
        {json.dumps(votes, ensure_ascii=False, indent=2)}

        Réponds EXCLUSIVEMENT avec un objet JSON valide suivant ce schéma strict :
        {{
          "scores": {{
            "FIS": 70,
            "ETA": 65,
            "REG": 68,
            "PRO": 60,
            "LIB": 62,
            "OUV": 58
          }},
          "score_global": 64,
          "qualification": "Modérément libéral",
          "synthese": "Explication synthétique de l'orientation économique observée dans ses votes."
        }}
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )

            analysis_result = json.loads(response.text)

            # Mise à jour des valeurs du député dans data.json
            depute["scores"] = analysis_result["scores"]
            depute["score_global"] = analysis_result.get("score_global", 50)
            depute["qualification"] = analysis_result.get("qualification", "Non évalué")
            depute["synthese_analyse"] = analysis_result.get("synthese", "")
            depute["votes"] = votes

            # Sauvegarde incrémentale immédiate (évite toute perte en cas de coupure)
            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(deputes_db, f, ensure_ascii=False, indent=2)

            print(f"  ✅ Score global : {depute['score_global']}/100 ({depute['qualification']})")
            print(f"  📊 Scores par pilier : {analysis_result['scores']}\n")

        except Exception as e:
            print(f"  ❌ Erreur lors de l'analyse de {nom} : {e}\n")

        # Pause pour éviter d'atteindre les limites de requêtes par minute (RPM)
        time.sleep(2)

    print("─" * 60)
    print("🎉 Analyse par lot terminée ! 'data.json' est entièrement à jour.")


if __name__ == "__main__":
    analyze_all_udr_votes()