import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Charge les variables d'environnement définies dans le fichier .env
load_dotenv()


def analyze_depute_votes(depute_id="gerault-verny"):
    # 1. Chargement des données
    with open("votes.json", "r", encoding="utf-8") as f:
        all_votes = json.load(f)

    with open("data.json", "r", encoding="utf-8") as f:
        deputes_db = json.load(f)

    votes = all_votes.get(depute_id, [])
    if not votes:
        print(f"❌ Aucun vote trouvé pour {depute_id} dans votes.json")
        return

    # 2. Préparation du client Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ GEMINI_API_KEY non trouvée dans le fichier .env")
        api_key = input("Entrez votre clé API Gemini : ").strip()

    client = genai.Client(api_key=api_key)

    # 3. Prompt d'analyse économique
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

    print(f"🤖 Analyse des votes de {depute_id} par Gemini...")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )

    analysis_result = json.loads(response.text)

    # 4. Injection dans data.json
    updated = False
    for depute in deputes_db:
        if depute["id"] == depute_id:
            depute["scores"] = analysis_result["scores"]
            depute["score_global"] = analysis_result.get("score_global", 50)
            depute["qualification"] = analysis_result.get(
                "qualification", "Non évalué"
            )
            depute["synthese_analyse"] = analysis_result.get("synthese", "")
            depute["votes"] = votes
            updated = True
            break

    if updated:
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(deputes_db, f, ensure_ascii=False, indent=2)
        print(f"✅ `data.json` mis à jour avec succès pour {depute_id} !")
        print(f"📊 Nouveaux scores : {analysis_result['scores']}")
    else:
        print(f"❌ Député {depute_id} non trouvé dans data.json")


if __name__ == "__main__":
    analyze_depute_votes("gerault-verny")