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
    """Charge le JSON existant pour ne pas perdre les scores et initiatives déjà saisis."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            items = json.load(f)
            return {item["id"]: item for item in items}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def fetch_and_update():
    existing_db = load_existing_data()

    # Simulation d'un navigateur pour éviter d'être bloqué (Erreur 403 / 404)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    # API Open Data de l'Assemblée nationale (17e législature)
    url = "https://raw.githubusercontent.com/datagouv/deputes-data/main/deputes.json"

    print(" Connexion à la base de données des députés...")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(
                f" Erreur HTTP {response.status_code} lors de la récupération."
            )
            return

        deputes_raw = response.json()
    except Exception as e:
        print(f" Impossible de contacter le serveur : {e}")
        return

    updated_list = []

    for item in deputes_raw:
        prenom = item.get("prenom", "")
        nom = item.get("nom", "")
        full_name = f"{prenom} {nom}".strip()

        if not full_name:
            continue

        depute_id = slugify(full_name)
        pa_id = item.get("id_an", "")

        # URL de la photo officielle AN
        photo_url = (
            f"https://www.assemblee-nationale.fr/dyn/static/tribun/17/photos/{pa_id}.jpg"
            if pa_id
            else ""
        )

        # Circonscription et groupe
        circo = (
            f"{item.get('nom_circo', '')} ({item.get('num_circo', '')}ᵉ)"
            if item.get("num_circo")
            else item.get("nom_circo", "Non renseignée")
        )
        groupe = item.get("groupe_abrev", "NI")

        # Fusion conservatrice avec les données manuelles existantes
        existing_record = existing_db.get(depute_id, {})

        depute_entry = {
            "id": depute_id,
            "pa_id": pa_id,
            "nom": full_name,
            "circo": existing_record.get("circo", circo),
            "groupe": existing_record.get("groupe", groupe),
            "photoUrl": existing_record.get(
                "photoUrl", photo_url or "assets/default-avatar.png"
            ),
            "datanUrl": existing_record.get(
                "datanUrl", f"https://datan.fr/deputes/depute_{depute_id}"
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
        f" Mise à jour réussie : {len(updated_list)} députés enregistrés dans data.json !"
    )


if __name__ == "__main__":
    fetch_and_update()