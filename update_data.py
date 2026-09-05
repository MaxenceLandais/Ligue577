import io
import json
import re
import unicodedata
import zipfile
import requests


def slugify(text):
    text = (
        unicodedata.normalize("NFD", text)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .lower()
    )
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def load_existing_data(filepath="data.json"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            items = json.load(f)
            return {item["id"]: item for item in items}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def fetch_and_update():
    existing_db = load_existing_data()

    # URL officielle valide du zip Open Data de l'Assemblée nationale
    url = "https://data.assemblee-nationale.fr/static/openData/repository/17/amo/deputes_actifs_mandats_actifs_organes/AMO10_deputes_actifs_mandats_actifs_organes.json.zip"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    print("Téléchargement du fichier Open Data officiel...")

    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(
                f"Erreur HTTP {response.status_code} lors du téléchargement."
            )
            return

        updated_list = []

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            for filename in z.namelist():
                if filename.endswith(".json") and (
                    "PA" in filename or "acteur" in filename
                ):
                    with z.open(filename) as f:
                        data = json.load(f)

                        acteur = data.get("acteur", {})
                        if not acteur and "export" in data:
                            acteur = data["export"].get("acteur", {})

                        if not acteur or not isinstance(acteur, dict):
                            continue

                        pa_id = acteur.get("uid", {}).get("#text", "")
                        etat_civil = (
                            acteur.get("etatCivil", {}).get("ident", {})
                        )
                        prenom = etat_civil.get("prenom", "")
                        nom = etat_civil.get("nom", "")
                        full_name = f"{prenom} {nom}".strip()

                        if not full_name or not pa_id:
                            continue

                        depute_id = slugify(full_name)
                        photo_url = f"https://www.assemblee-nationale.fr/dyn/static/tribun/17/photos/{pa_id}.jpg"

                        existing_record = existing_db.get(depute_id, {})

                        depute_entry = {
                            "id": depute_id,
                            "pa_id": pa_id,
                            "nom": full_name,
                            "circo": existing_record.get(
                                "circo", "Non renseignée"
                            ),
                            "groupe": existing_record.get("groupe", "NI"),
                            "photoUrl": existing_record.get(
                                "photoUrl", photo_url
                            ),
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
                            "initiatives": existing_record.get(
                                "initiatives", []
                            ),
                        }
                        updated_list.append(depute_entry)

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(updated_list, f, ensure_ascii=False, indent=2)

        print(
            f"Mise à jour réussie : {len(updated_list)} députés enregistrés dans data.json !"
        )

    except Exception as e:
        print(f"Erreur lors du traitement : {e}")


if __name__ == "__main__":
    fetch_and_update()