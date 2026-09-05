import json
import re
import unicodedata
import requests


def slugify(text):
    """Transforme 'Bernard Chaix' en 'bernard-chaix'."""
    text = (
        unicodedata.normalize("NFD", text)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .lower()
    )
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def load_existing_data(filepath="data.json"):
    """Charge le JSON existant sous forme de dictionnaire indexé par ID."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            items = json.load(f)
            return {item["id"]: item for item in items}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def fetch_and_update():
    existing_db = load_existing_data()

    # API Open Data de l'Assemblée nationale (liste des acteurs)
    url = "https://www.assemblee-nationale.fr/dyn/static/tribun/17/json/acteurs.json"
    response = requests.get(url)

    if response.status_code != 200:
        print(
            f"Erreur lors de la récupération des données : {response.status_code}"
        )
        return

    data = response.json()
    acteurs = data.get("export", {}).get("acteurs", {}).get("acteur", [])

    updated_list = []

    for acteur in acteurs:
        # Vérification si le député est actuellement en mandat
        mats = acteur.get("mandats", {}).get("mandat", [])
        if isinstance(mats, dict):
            mats = [mats]

        est_depute_actif = any(
            m.get("typeOrgane") == "ASSEMBLEE" and m.get("dateFin") is None
            for m in mats
        )
        if not est_depute_actif:
            continue

        pa_id = acteur.get("uid", {}).get("#text")
        etat_civil = acteur.get("etatCivil", {}).get("ident", {})
        prenom = etat_civil.get("prenom")
        nom = etat_civil.get("nom")
        full_name = f"{prenom} {nom}"
        depute_id = slugify(full_name)

        # Photo CDN officielle
        photo_url = f"https://www.assemblee-nationale.fr/dyn/static/tribun/17/photos/{pa_id}.jpg"

        # Conservation des données saisies manuellement (scores, initiatives, réseaux)
        existing_record = existing_db.get(depute_id, {})

        depute_entry = {
            "id": depute_id,
            "pa_id": pa_id,
            "nom": full_name,
            "circo": existing_record.get(
                "circo", "Non renseignée"
            ),  # Extrait du mandat
            "groupe": existing_record.get("groupe", "NI"),
            "photoUrl": photo_url,
            "datanUrl": existing_record.get(
                "datanUrl",
                f"https://datan.fr/deputes/depute_{depute_id}",
            ),
            "scores": existing_record.get(
                "scores",
                {
                    "FIS": 50,
                    "ETA": 50,
                    "REG": 50,
                    "PRO": 50,
                    "LIB": 50,
                    "OUV": 50,
                },
            ),
            "reseaux": existing_record.get("reseaux", {}),
            "initiatives": existing_record.get("initiatives", []),
        }

        updated_list.append(depute_entry)

    # Sauvegarde dans data.json
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(updated_list, f, ensure_ascii=False, indent=2)

    print(
        f"Base de données mise à jour avec succès ({len(updated_list)} députés)."
    )


if __name__ == "__main__":
    fetch_and_update()