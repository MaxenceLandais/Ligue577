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


def extract_social_links(adresses_data, existing_reseaux):
    """Extrait les URL officielles des réseaux sociaux depuis la fiche de l'Assemblée Nationale."""
    reseaux = existing_reseaux if isinstance(existing_reseaux, dict) else {}

    adresses = adresses_data.get("adresse", [])
    if isinstance(adresses, dict):
        adresses = [adresses]

    for addr in adresses:
        type_code = addr.get("typeCode", "")
        url = addr.get("valUrl") or addr.get("valTexte") or ""

        if not url:
            continue

        # Nettoyage et uniformisation de l'URL
        if "twitter.com" in url or "x.com" in url or type_code == "TWITTER":
            if not url.startswith("http"):
                url = f"https://x.com/{url.lstrip('@')}"
            prev_abonnees = reseaux.get("x", {}).get("abonnees", 0)
            reseaux["x"] = {"url": url, "abonnees": prev_abonnees}

        elif "facebook.com" in url or type_code == "FACEBOOK":
            if not url.startswith("http"):
                url = f"https://www.facebook.com/{url}"
            prev_abonnees = reseaux.get("facebook", {}).get("abonnees", 0)
            reseaux["facebook"] = {"url": url, "abonnees": prev_abonnees}

        elif "linkedin.com" in url or type_code == "LINKEDIN":
            if not url.startswith("http"):
                url = f"https://www.linkedin.com/in/{url}"
            prev_abonnees = reseaux.get("linkedin", {}).get("abonnees", 0)
            reseaux["linkedin"] = {"url": url, "abonnees": prev_abonnees}

    return reseaux


def extract_circo(mandats_data):
    """Extrait la circonscription exacte du mandat de député actif."""
    mandats = mandats_data.get("mandat", [])
    if isinstance(mandats, dict):
        mandats = [mandats]

    for m in mandats:
        if m.get("typeOrgane") == "ASSEMBLEE" and m.get("dateFin") is None:
            election = m.get("election", {}).get("lieu", {})
            dept = election.get("departement", "")
            num_circo = election.get("numCirco", "")
            if dept and num_circo:
                return f"{dept} ({num_circo}ᵉ)"
            elif dept:
                return dept
    return "Non renseignée"


def fetch_and_update():
    existing_db = load_existing_data()

    url = "https://data.assemblee-nationale.fr/static/openData/repository/17/amo/deputes_actifs_mandats_actifs_organes/AMO10_deputes_actifs_mandats_actifs_organes.json.zip"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    print(
        "⚡ Téléchargement et traitement des fiches officielles des députés..."
    )

    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(
                f"❌ Erreur HTTP {response.status_code} lors du téléchargement."
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
                        existing_record = existing_db.get(depute_id, {})

                        # Extractions automatisées
                        circo = extract_circo(acteur.get("mandats", {}))
                        reseaux = extract_social_links(
                            acteur.get("adresses", {}),
                            existing_record.get("reseaux", {}),
                        )

                        photo_url = f"https://www.assemblee-nationale.fr/dyn/static/tribun/17/photos/{pa_id}.jpg"
                        datan_url = f"https://datan.fr/deputes/depute_{depute_id}"

                        depute_entry = {
                            "id": depute_id,
                            "pa_id": pa_id,
                            "nom": full_name,
                            "circo": (
                                existing_record.get("circo")
                                if existing_record.get("circo")
                                != "Non renseignée"
                                else circo
                            ),
                            "groupe": existing_record.get("groupe", "NI"),
                            "photoUrl": existing_record.get(
                                "photoUrl", photo_url
                            ),
                            "datanUrl": existing_record.get(
                                "datanUrl", datan_url
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
                            "reseaux": reseaux,
                            "initiatives": existing_record.get(
                                "initiatives", []
                            ),
                        }
                        updated_list.append(depute_entry)

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(updated_list, f, ensure_ascii=False, indent=2)

        print(
            f"✅ Mise à jour terminée : {len(updated_list)} députés enregistrés avec leurs circonscriptions et réseaux sociaux officiels !"
        )

    except Exception as e:
        print(f"❌ Erreur lors du traitement : {e}")


if __name__ == "__main__":
    fetch_and_update()