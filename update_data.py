import io
import json
import re
import unicodedata
import zipfile
import requests

UDR_SLUGS = {
    "eric-ciotti",
    "alexandre-allegret-pilot",
    "charles-alloncle",
    "matthieu-bloch",
    "pierre-henri-carbonnel",
    "bernard-chaix",
    "marc-chavent",
    "christelle-d-intorni",
    "christelle-dintorni",
    "olivier-fayssat",
    "bartolome-lenoir",
    "hanane-mansouri",
    "maxime-michelet",
    "eric-michoux",
    "sophie-vaginay",
    "sophie-ricourt-vaginay",
    "sophie-dumont",
    "vincent-trebuchet",
    "antoine-valentin",
    "gerault-verny",
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


def extract_groupes_map(z):
    groupes_map = {}
    for filename in z.namelist():
        if filename.endswith(".json") and ("PO" in filename or "organe" in filename):
            try:
                with z.open(filename) as f:
                    data = json.load(f)
                    organe = data.get("organe", {})
                    if not organe and "export" in data:
                        organe = data["export"].get("organe", {})

                    if isinstance(organe, dict) and organe.get("codeType") == "GP":
                        uid = organe.get("uid")
                        abrev = organe.get("libelleAbrev") or organe.get("libelle") or ""
                        if abrev.upper() in ["UDDPLR", "UDR"]:
                            abrev = "UDR"
                        if uid and abrev:
                            groupes_map[uid] = abrev
            except Exception:
                continue
    return groupes_map


def parse_an_acteur(acteur, existing_record, groupes_map):
    profession = "Non renseignée"
    prof_data = acteur.get("profession")
    if isinstance(prof_data, dict):
        profession = (
            prof_data.get("libelleCourant")
            or prof_data.get("socioPro")
            or prof_data.get("libelle")
            or "Non renseignée"
        )
    elif isinstance(prof_data, str) and prof_data.strip():
        profession = prof_data.strip()

    # Nettoyage du préfixe "(23) - "
    profession = re.sub(r"^\(\d+\)\s*-\s*", "", profession)

    groupe = existing_record.get("groupe", "NI")
    mandats = acteur.get("mandats", {}).get("mandat", [])
    if isinstance(mandats, dict):
        mandats = [mandats]

    for m in mandats:
        if isinstance(m, dict) and m.get("typeOrgane") == "GP" and m.get("dateFin") is None:
            organes = m.get("organes", {})
            ref = organes.get("organeRef", "") if isinstance(organes, dict) else ""
            if ref in groupes_map:
                groupe = groupes_map[ref]
                break

    email = ""
    reseaux = {}

    adresses = acteur.get("adresses", {}).get("adresse", [])
    if isinstance(adresses, dict):
        adresses = [adresses]

    for addr in adresses:
        if not isinstance(addr, dict):
            continue

        type_lib = str(addr.get("typeLibelle", "")).lower()
        val_elec = addr.get("valElec", "") or addr.get("urlDeRattachement", "")

        if "electronique" in type_lib or "email" in type_lib or "courriel" in type_lib:
            if val_elec and not email:
                email = val_elec.replace("mailto:", "").strip()

        if val_elec:
            val_lower = val_elec.lower()
            if "twitter.com" in val_lower or "x.com" in val_lower:
                reseaux["x"] = {"url": val_elec}
            elif "facebook.com" in val_lower:
                reseaux["facebook"] = {"url": val_elec}
            elif "linkedin.com" in val_lower:
                reseaux["linkedin"] = {"url": val_elec}
            elif "instagram.com" in val_lower:
                reseaux["instagram"] = {"url": val_elec}

    return profession, groupe, email, reseaux


def fetch_and_update():
    existing_db = load_existing_data()

    url = "https://data.assemblee-nationale.fr/static/openData/repository/17/amo/deputes_actifs_mandats_actifs_organes/AMO10_deputes_actifs_mandats_actifs_organes.json.zip"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    print("⚡ Téléchargement et traitement OpenData...")

    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"❌ Erreur HTTP {response.status_code}")
            return

        updated_list = []

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            groupes_map = extract_groupes_map(z)

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

                        uid_raw = acteur.get("uid")
                        if isinstance(uid_raw, dict):
                            pa_id = uid_raw.get("#text", "")
                        elif isinstance(uid_raw, str):
                            pa_id = uid_raw
                        else:
                            pa_id = ""

                        etat_civil = acteur.get("etatCivil", {}).get("ident", {})
                        prenom = etat_civil.get("prenom", "")
                        nom = etat_civil.get("nom", "")
                        full_name = f"{prenom} {nom}".strip()

                        if not full_name or not pa_id:
                            continue

                        depute_id = slugify(full_name)
                        existing_record = existing_db.get(depute_id, {})

                        prof_an, groupe_an, email_an, reseaux_an = parse_an_acteur(
                            acteur, existing_record, groupes_map
                        )

                        if depute_id in UDR_SLUGS or groupe_an in ["UDR", "UDDPLR"]:
                            groupe_an = "UDR"

                        photo_url = f"https://www.assemblee-nationale.fr/dyn/static/tribun/17/photos/{pa_id}.jpg"
                        datan_url = existing_record.get("datanUrl") or f"https://datan.fr/deputes/depute_{depute_id}"

                        reseaux = existing_record.get("reseaux", {})
                        if not isinstance(reseaux, dict):
                            reseaux = {}
                        for k, v in reseaux_an.items():
                            reseaux[k] = v

                        old_stats = existing_record.get("stats") or {}

                        depute_entry = {
                            "id": depute_id,
                            "pa_id": pa_id,
                            "nom": full_name,
                            "circo": existing_record.get("circo", "Non renseignée"),
                            "groupe": groupe_an,
                            "email": email_an or existing_record.get("email", ""),
                            "profession": prof_an if prof_an != "Non renseignée" else existing_record.get("profession", "Non renseignée"),
                            "stats": {
                                "participation": old_stats.get("participation", 0),
                                "loyaute_groupe": old_stats.get("loyaute_groupe", 0),
                            },
                            "photoUrl": photo_url,
                            "photo": photo_url,
                            "avatar": photo_url,
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
                except Exception:
                    continue

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(updated_list, f, ensure_ascii=False, indent=2)

        udr_count = sum(1 for d in updated_list if d["groupe"] == "UDR")

        print("✅ Mis à jour avec succès !")
        print(f"📊 Total députés : {len(updated_list)}")
        print(f"🇫🇷 Députés UDR identifiés : {udr_count}")

    except Exception as e:
        print(f"❌ Erreur : {e}")


if __name__ == "__main__":
    fetch_and_update()