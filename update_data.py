import io
import json
import re
import unicodedata
import zipfile
import requests
from bs4 import BeautifulSoup


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


def scrape_datan_info(depute_slug):
    """Scrape la fiche Datan du député pour récupérer : email, réseaux, profession, stats."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    url = f"https://datan.fr/deputes/depute_{depute_slug}"

    data_scraped = {
        "email": "",
        "profession": "",
        "age": None,
        "participation": None,
        "loyaute_groupe": None,
        "reseaux": {},
    }

    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code != 200:
            return data_scraped

        soup = BeautifulSoup(res.content, "html.parser")

        # 1. Réseaux sociaux & Email
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "mailto:" in href and not data_scraped["email"]:
                data_scraped["email"] = href.replace("mailto:", "").strip()
            elif "twitter.com" in href or "x.com" in href:
                data_scraped["reseaux"]["x"] = href
            elif "facebook.com" in href:
                data_scraped["reseaux"]["facebook"] = href
            elif "linkedin.com" in href:
                data_scraped["reseaux"]["linkedin"] = href
            elif "instagram.com" in href:
                data_scraped["reseaux"]["instagram"] = href

        # 2. Statistiques (Participation & Loyauté)
        text_content = soup.get_text()

        part_match = re.search(
            r"participé à\s*(\d+)%\s*des votes", text_content
        )
        if part_match:
            data_scraped["participation"] = int(part_match.group(1))

        loy_match = re.search(
            r"voté sur la même ligne que son groupe politique dans\s*(\d+)%",
            text_content,
        )
        if loy_match:
            data_scraped["loyaute_groupe"] = int(loy_match.group(1))

        # 3. Profession d'origine
        prof_match = re.search(
            r"exerçait le métier [^\-]*-\s*([^.]+)\.", text_content
        )
        if prof_match:
            data_scraped["profession"] = prof_match.group(1).strip().capitalize()

    except Exception as e:
        print(f"⚠️ Datan fetch omit pour {depute_slug}: {e}")

    return data_scraped


def fetch_and_update():
    existing_db = load_existing_data()

    url = "https://data.assemblee-nationale.fr/static/openData/repository/17/amo/deputes_actifs_mandats_actifs_organes/AMO10_deputes_actifs_mandats_actifs_organes.json.zip"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    print("⚡ Téléchargement de la base Assemblée Nationale & Datan.fr...")

    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"❌ Erreur HTTP {response.status_code}")
            return

        updated_list = []

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            json_files = [
                f
                for f in z.namelist()
                if f.endswith(".json") and ("PA" in f or "acteur" in f)
            ]
            print(
                f"📋 {len(json_files)} fiches trouvées. Enrichissement en cours..."
            )

            for idx, filename in enumerate(json_files, 1):
                with z.open(filename) as f:
                    data = json.load(f)
                    acteur = data.get("acteur", {})
                    if not acteur and "export" in data:
                        acteur = data["export"].get("acteur", {})

                    if not acteur or not isinstance(acteur, dict):
                        continue

                    pa_id = acteur.get("uid", {}).get("#text", "")
                    etat_civil = acteur.get("etatCivil", {}).get("ident", {})
                    prenom = etat_civil.get("prenom", "")
                    nom = etat_civil.get("nom", "")
                    full_name = f"{prenom} {nom}".strip()

                    if not full_name or not pa_id:
                        continue

                    depute_id = slugify(full_name)
                    existing_record = existing_db.get(depute_id, {})

                    # Enrichissement Datan.fr
                    datan_data = scrape_datan_info(depute_id)

                    # Photos et liens
                    photo_url = f"https://www.assemblee-nationale.fr/dyn/static/tribun/17/photos/{pa_id}.jpg"
                    datan_url = f"https://datan.fr/deputes/depute_{depute_id}"

                    # Merge réseaux
                    reseaux = existing_record.get("reseaux", {})
                    for k, v in datan_data["reseaux"].items():
                        reseaux[k] = {"url": v}

                    depute_entry = {
                        "id": depute_id,
                        "pa_id": pa_id,
                        "nom": full_name,
                        "circo": existing_record.get("circo", "Non renseignée"),
                        "groupe": existing_record.get("groupe", "NI"),
                        "email": datan_data["email"]
                        or existing_record.get("email", ""),
                        "profession": datan_data["profession"]
                        or existing_record.get("profession", "Non renseignée"),
                        "stats": {
                            "participation": datan_data["participation"]
                            or existing_record.get("stats", {}).get(
                                "participation", 0
                            ),
                            "loyaute_groupe": datan_data["loyaute_groupe"]
                            or existing_record.get("stats", {}).get(
                                "loyaute_groupe", 0
                            ),
                        },
                        "photoUrl": photo_url,
                        "datanUrl": datan_url,
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
                        "initiatives": existing_record.get("initiatives", []),
                    }

                    updated_list.append(depute_entry)

                    if idx % 50 == 0:
                        print(f"➜ {idx}/{len(json_files)} députés traités...")

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(updated_list, f, ensure_ascii=False, indent=2)

        print(
            f"✅ Succès ! {len(updated_list)} députés enrichis enregistrés dans data.json"
        )

    except Exception as e:
        print(f"❌ Erreur : {e}")


if __name__ == "__main__":
    fetch_and_update()