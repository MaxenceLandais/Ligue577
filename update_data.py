import io
import json
import re
import time
import unicodedata
import zipfile
import requests
from bs4 import BeautifulSoup

# Liste stricte des slugs des députés UDR (17e législature)
UDR_SLUGS = {
    "eric-ciotti",
    "christelle-d-intorni",
    "christelle-dintorni",
    "bernard-chaix",
    "gerault-verny",
    "hanane-mansouri",
    "charles-alloncle",
    "vincent-trebuchet",
    "alexandre-allegret-pilot",
    "sophie-dumont",
    "brigitte-bareges",
    "matthieu-bloch",
    "marc-chavent",
    "eric-michoux",
    "typhanie-degois",
    "thierry-perez",
    "monique-griseti",
}


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
    except Exception:
        return {}


def scrape_datan_info(depute_slug):
    """Scrape la fiche Datan avec gestion sécurisée des erreurs."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    url = f"https://datan.fr/deputes/depute_{depute_slug}"

    data_scraped = {
        "email": "",
        "profession": "",
        "participation": None,
        "loyaute_groupe": None,
        "reseaux": {},
    }

    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code != 200:
            return data_scraped

        soup = BeautifulSoup(res.content, "html.parser")

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

        prof_match = re.search(
            r"exerçait le métier [^\-]*-\s*([^.]+)\.", text_content
        )
        if prof_match:
            data_scraped["profession"] = (
                prof_match.group(1).strip().capitalize()
            )

    except Exception:
        pass

    return data_scraped


def fetch_and_update():
    existing_db = load_existing_data()

    url = "https://data.assemblee-nationale.fr/static/openData/repository/17/amo/deputes_actifs_mandats_actifs_organes/AMO10_deputes_actifs_mandats_actifs_organes.json.zip"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    print("⚡ Traitement ciblé EXCLUSIVEMENT pour les députés UDR...")

    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"❌ Erreur HTTP {response.status_code}")
            return

        updated_list = []
        udr_count = 0

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            json_files = [
                f
                for f in z.namelist()
                if f.endswith(".json") and ("PA" in f or "acteur" in f)
            ]

            for filename in json_files:
                try:
                    with z.open(filename) as f:
                        data = json.load(f)
                        acteur = data.get("acteur", {})
                        if not acteur and "export" in data:
                            acteur = data["export"].get("acteur", {})

                        if not acteur or not isinstance(acteur, dict):
                            continue

                        pa_id = acteur.get("uid", {}).get("#text", "")
                        etat_civil = acteur.get("etatCivil", {}).get(
                            "ident", {}
                        )
                        prenom = etat_civil.get("prenom", "")
                        nom = etat_civil.get("nom", "")
                        full_name = f"{prenom} {nom}".strip()

                        if not full_name or not pa_id:
                            continue

                        depute_id = slugify(full_name)
                        existing_record = existing_db.get(depute_id, {})

                        # VÉRIFICATION STRICTE DE L'APPARTENANCE UDR
                        is_udr = depute_id in UDR_SLUGS

                        if is_udr:
                            udr_count += 1
                            groupe = "UDR"
                            print(
                                f"🔎 [{udr_count}] Enrichissement UDR : {full_name}"
                            )
                            datan_data = scrape_datan_info(depute_id)
                            time.sleep(0.2)
                        else:
                            # Remet à "NI" ou autre si ce n'est pas un UDR
                            prev_groupe = existing_record.get("groupe", "NI")
                            groupe = (
                                prev_groupe if prev_groupe != "UDR" else "NI"
                            )

                            old_stats = existing_record.get("stats") or {}
                            datan_data = {
                                "email": existing_record.get("email", ""),
                                "profession": existing_record.get(
                                    "profession", "Non renseignée"
                                ),
                                "participation": old_stats.get(
                                    "participation", 0
                                ),
                                "loyaute_groupe": old_stats.get(
                                    "loyaute_groupe", 0
                                ),
                                "reseaux": {},
                            }

                        photo_url = f"https://www.assemblee-nationale.fr/dyn/static/tribun/17/photos/{pa_id}.jpg"
                        datan_url = (
                            f"https://datan.fr/deputes/depute_{depute_id}"
                        )

                        reseaux = existing_record.get("reseaux", {})
                        if isinstance(datan_data.get("reseaux"), dict):
                            for k, v in datan_data["reseaux"].items():
                                reseaux[k] = {"url": v}

                        old_stats = existing_record.get("stats") or {}

                        depute_entry = {
                            "id": depute_id,
                            "pa_id": pa_id,
                            "nom": full_name,
                            "circo": existing_record.get(
                                "circo", "Non renseignée"
                            ),
                            "groupe": groupe,
                            "email": datan_data["email"]
                            or existing_record.get("email", ""),
                            "profession": datan_data["profession"]
                            or existing_record.get(
                                "profession", "Non renseignée"
                            ),
                            "stats": {
                                "participation": datan_data["participation"]
                                if datan_data["participation"] is not None
                                else old_stats.get("participation", 0),
                                "loyaute_groupe": datan_data["loyaute_groupe"]
                                if datan_data["loyaute_groupe"] is not None
                                else old_stats.get("loyaute_groupe", 0),
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
                            "initiatives": existing_record.get(
                                "initiatives", []
                            ),
                        }

                        updated_list.append(depute_entry)
                except Exception:
                    continue

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(updated_list, f, ensure_ascii=False, indent=2)

        print(
            f"\n✅ Succès ! Seuls les {udr_count} députés UDR ont été enrichis sans erreur."
        )

    except Exception as e:
        print(f"❌ Erreur générale : {e}")


if __name__ == "__main__":
    fetch_and_update()