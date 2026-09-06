import io
import json
import os
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
    "sophie-vaginay-ricourt",
    "sophie-ricourt-vaginay",
    "sophie-dumont",
    "vincent-trebuchet",
    "antoine-valentin",
    "gerault-verny",
}

# Dictionnaire de correspondance Département -> Région (pour cibler le bon blason)
DEPT_TO_REGION = {
    "Ain": "Auvergne-Rhône-Alpes",
    "Allier": "Auvergne-Rhône-Alpes",
    "Ardèche": "Auvergne-Rhône-Alpes",
    "Cantal": "Auvergne-Rhône-Alpes",
    "Drôme": "Auvergne-Rhône-Alpes",
    "Isère": "Auvergne-Rhône-Alpes",
    "Loire": "Auvergne-Rhône-Alpes",
    "Haute-Loire": "Auvergne-Rhône-Alpes",
    "Puy-de-Dôme": "Auvergne-Rhône-Alpes",
    "Rhône": "Auvergne-Rhône-Alpes",
    "Savoie": "Auvergne-Rhône-Alpes",
    "Haute-Savoie": "Auvergne-Rhône-Alpes",
    "Côte-d'Or": "Bourgogne-Franche-Comté",
    "Doubs": "Bourgogne-Franche-Comté",
    "Jura": "Bourgogne-Franche-Comté",
    "Nièvre": "Bourgogne-Franche-Comté",
    "Haute-Saône": "Bourgogne-Franche-Comté",
    "Saône-et-Loire": "Bourgogne-Franche-Comté",
    "Yonne": "Bourgogne-Franche-Comté",
    "Territoire de Belfort": "Bourgogne-Franche-Comté",
    "Côtes-d'Armor": "Bretagne",
    "Finistère": "Bretagne",
    "Ille-et-Vilaine": "Bretagne",
    "Morbihan": "Bretagne",
    "Cher": "Centre-Val de Loire",
    "Eure-et-Loir": "Centre-Val de Loire",
    "Indre": "Centre-Val de Loire",
    "Indre-et-Loire": "Centre-Val de Loire",
    "Loir-et-Cher": "Centre-Val de Loire",
    "Loiret": "Centre-Val de Loire",
    "Corse-du-Sud": "Corse",
    "Haute-Corse": "Corse",
    "Ardennes": "Grand Est",
    "Aube": "Grand Est",
    "Marne": "Grand Est",
    "Haute-Marne": "Grand Est",
    "Meurthe-et-Moselle": "Grand Est",
    "Meuse": "Grand Est",
    "Moselle": "Grand Est",
    "Bas-Rhin": "Grand Est",
    "Haut-Rhin": "Grand Est",
    "Vosges": "Grand Est",
    "Aisne": "Hauts-de-France",
    "Nord": "Hauts-de-France",
    "Oise": "Hauts-de-France",
    "Pas-de-Calais": "Hauts-de-France",
    "Somme": "Hauts-de-France",
    "Paris": "Île-de-France",
    "Seine-et-Marne": "Île-de-France",
    "Yvelines": "Île-de-France",
    "Essonne": "Île-de-France",
    "Hauts-de-Seine": "Île-de-France",
    "Seine-Saint-Denis": "Île-de-France",
    "Val-de-Marne": "Île-de-France",
    "Val-d'Oise": "Île-de-France",
    "Calvados": "Normandie",
    "Eure": "Normandie",
    "Manche": "Normandie",
    "Orne": "Normandie",
    "Seine-Maritime": "Normandie",
    "Charente": "Nouvelle-Aquitaine",
    "Charente-Maritime": "Nouvelle-Aquitaine",
    "Corrèze": "Nouvelle-Aquitaine",
    "Creuse": "Nouvelle-Aquitaine",
    "Dordogne": "Nouvelle-Aquitaine",
    "Gironde": "Nouvelle-Aquitaine",
    "Landes": "Nouvelle-Aquitaine",
    "Lot-et-Garonne": "Nouvelle-Aquitaine",
    "Pyrénées-Atlantiques": "Nouvelle-Aquitaine",
    "Deux-Sèvres": "Nouvelle-Aquitaine",
    "Vienne": "Nouvelle-Aquitaine",
    "Haute-Vienne": "Nouvelle-Aquitaine",
    "Ariège": "Occitanie",
    "Aude": "Occitanie",
    "Aveyron": "Occitanie",
    "Gard": "Occitanie",
    "Haute-Garonne": "Occitanie",
    "Gers": "Occitanie",
    "Hérault": "Occitanie",
    "Lot": "Occitanie",
    "Lozère": "Occitanie",
    "Hautes-Pyrénées": "Occitanie",
    "Pyrénées-Orientales": "Occitanie",
    "Tarn": "Occitanie",
    "Tarn-et-Garonne": "Occitanie",
    "Loire-Atlantique": "Pays de la Loire",
    "Maine-et-Loire": "Pays de la Loire",
    "Mayenne": "Pays de la Loire",
    "Sarthe": "Pays de la Loire",
    "Vendée": "Pays de la Loire",
    "Alpes-de-Haute-Provence": "Provence-Alpes-Côte d'Azur",
    "Hautes-Alpes": "Provence-Alpes-Côte d'Azur",
    "Alpes-Maritimes": "Provence-Alpes-Côte d'Azur",
    "Bouches-du-Rhône": "Provence-Alpes-Côte d'Azur",
    "Var": "Provence-Alpes-Côte d'Azur",
    "Vaucluse": "Provence-Alpes-Côte d'Azur",
    "Guadeloupe": "Guadeloupe",
    "Martinique": "Martinique",
    "Guyane": "Guyane",
    "La Réunion": "La Réunion",
    "Mayotte": "Mayotte",
    "Nouvelle-Calédonie": "Nouvelle-Calédonie",
    "Polynésie française": "Polynésie française",
    "Saint-Barthélemy et Saint-Martin": "Guadeloupe",
    "Saint-Pierre-et-Miquelon": "Normandie",
}


def slugify(text: str) -> str:
    """Slug générique pour les identifiants internes et les départements."""
    text = (
        unicodedata.normalize("NFD", text)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .lower()
    )
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def slugify_asset(text: str) -> str:
    """Slug avec underscores pour correspondre aux noms de fichiers dans assets/."""
    if not text:
        return ""
    text = unicodedata.normalize("NFD", str(text))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn").lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "_", text).strip("_")


def clean_alpha_only(text: str) -> str:
    """Ne garde que les lettres minuscules (supprime accents, tirets, apostrophes, espaces)."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-zA-Z]", "", text).lower()


def build_datan_slug(full_name: str) -> str:
    """Génère le slug strict Datan : prenom-nom (prenom et nom tout attachés)."""
    parts = full_name.strip().split(maxsplit=1)
    if not parts:
        return ""
    prenom = parts[0]
    nom_famille = parts[1] if len(parts) > 1 else ""

    prenom_slug = clean_alpha_only(prenom)
    nom_slug = clean_alpha_only(nom_famille)

    return f"{prenom_slug}-{nom_slug}" if nom_slug else prenom_slug


def get_wikipedia_bio_intro(nom_depute: str) -> str:
    """
    Récupère L'INTÉGRALITÉ du résumé introductif
    de la page Wikipédia du député, avant le premier chapitre.
    """
    url = "https://fr.wikipedia.org/w/api.php"

    titles_to_try = [
        nom_depute,
        f"{nom_depute} (homme politique)",
        f"{nom_depute} (femme politique)",
        f"{nom_depute} (politique)",
    ]

    headers = {
        "User-Agent": "ObservatoireLiberalismeBot/1.0 (contact@votre-domaine.fr)"
    }

    for title in titles_to_try:
        params = {
            "action": "query",
            "prop": "extracts",
            "exintro": "1",
            "explaintext": "1",
            "titles": title,
            "format": "json",
            "redirects": "1",
        }
        try:
            res = requests.get(url, params=params, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                pages = data.get("query", {}).get("pages", {})
                for page_id, page_data in pages.items():
                    if page_id != "-1":
                        extract = page_data.get("extract", "").strip()
                        if extract and "peut désigner" not in extract[:120].lower():
                            return re.sub(r"\s+", " ", extract)
        except Exception:
            pass

    return ""


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
                        abrev = (
                            organe.get("libelleAbrev")
                            or organe.get("libelle")
                            or ""
                        )
                        if abrev.upper() in ["UDDPLR", "UDR", "UDR-R"]:
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

    profession = re.sub(r"^\(\d+\)\s*-\s*", "", profession)

    groupe = existing_record.get("groupe", "NI")
    dept_name = ""
    num_dept = ""
    num_circo = ""

    mandats = acteur.get("mandats", {}).get("mandat", [])
    if isinstance(mandats, dict):
        mandats = [mandats]

    for m in mandats:
        if not isinstance(m, dict):
            continue
        type_organe = m.get("typeOrgane")
        date_fin = m.get("dateFin")

        if type_organe == "GP" and date_fin is None:
            organes = m.get("organes", {})
            ref = (
                organes.get("organeRef", "") if isinstance(organes, dict) else ""
            )
            if ref in groupes_map:
                groupe = groupes_map[ref]

        if type_organe == "ASSEMBLEE" and date_fin is None:
            lieu = m.get("election", {}).get("lieu", {})
            if isinstance(lieu, dict):
                dept_name = lieu.get("departement", "") or ""
                num_dept = str(lieu.get("numDepartement", "") or "")
                num_circo = str(lieu.get("numCirco", "") or "")

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

    return profession, groupe, email, reseaux, dept_name, num_dept, num_circo


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

                        etat_civil = acteur.get("etatCivil", {})
                        ident = etat_civil.get("ident", {})
                        prenom = ident.get("prenom", "")
                        nom = ident.get("nom", "")
                        full_name = f"{prenom} {nom}".strip()

                        # Extraction date de naissance
                        info_nais = etat_civil.get("infoNaissance", {})
                        date_naissance = (
                            info_nais.get("dateNais", "")
                            if isinstance(info_nais, dict)
                            else ""
                        )

                        if not full_name or not pa_id:
                            continue

                        depute_id = slugify(full_name)
                        existing_record = existing_db.get(depute_id, {})

                        (
                            prof_an,
                            groupe_an,
                            email_an,
                            reseaux_an,
                            dept_name,
                            num_dept,
                            num_circo,
                        ) = parse_an_acteur(acteur, existing_record, groupes_map)

                        is_udr = (
                            depute_id in UDR_SLUGS
                            or groupe_an in ["UDR", "UDDPLR", "UDR-R"]
                        )
                        if is_udr:
                            groupe_an = "UDR"

                        # Lien Datan
                        datan_slug = build_datan_slug(full_name)
                        if dept_name and num_dept:
                            dept_slug = slugify(dept_name)
                            num_dept_fmt = (
                                num_dept.zfill(2)
                                if num_dept.isdigit() and len(num_dept) == 1
                                else num_dept
                            )
                            datan_url = f"https://datan.fr/deputes/{dept_slug}-{num_dept_fmt}/depute_{datan_slug}"
                        else:
                            datan_url = (
                                existing_record.get("datanUrl")
                                or f"https://datan.fr/deputes/depute_{datan_slug}"
                            )

                        # Circonscription et Région
                        circo_val = existing_record.get("circo")
                        if not circo_val or circo_val == "Non renseignée":
                            if dept_name and num_circo:
                                circo_val = f"{dept_name} ({num_circo}e)"
                            else:
                                circo_val = dept_name or "Non renseignée"

                        region_val = existing_record.get(
                            "region"
                        ) or DEPT_TO_REGION.get(dept_name, dept_name)

                        # Intro Wikipédia
                        biographie = existing_record.get("biographie", "")
                        if is_udr:
                            print(
                                f"   ➔ Récupération de l'intro Wikipédia : {full_name}"
                            )
                            bio_intro = get_wikipedia_bio_intro(full_name)
                            if bio_intro:
                                biographie = bio_intro

                        # --- RÉSOLUTION DES ASSETS LOCAUX ---
                        # 1. Photo du député
                        local_photo = os.path.join(
                            "assets", "deputes", f"{depute_id}.jpg"
                        )
                        online_photo = f"https://www.assemblee-nationale.fr/dyn/static/tribun/17/photos/{pa_id}.jpg"
                        photo_url = (
                            local_photo.replace("\\", "/")
                            if os.path.exists(local_photo)
                            else online_photo
                        )

                        # 2. Blason de la région
                        region_slug = slugify_asset(region_val)
                        local_blason = os.path.join(
                            "assets", "regions", f"{region_slug}.png"
                        )
                        blason_url = (
                            local_blason.replace("\\", "/")
                            if os.path.exists(local_blason)
                            else None
                        )

                        # 3. Logo du parti / groupe
                        parti_slug = slugify_asset(groupe_an)
                        local_logo = os.path.join(
                            "assets", "partis", f"{parti_slug}.png"
                        )
                        logo_parti_url = (
                            local_logo.replace("\\", "/")
                            if os.path.exists(local_logo)
                            else None
                        )

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
                            "date_naissance": (
                                date_naissance
                                or existing_record.get("date_naissance", "")
                            ),
                            "region": region_val,
                            "dept": dept_name,
                            "circo": circo_val,
                            "groupe": groupe_an,
                            "email": email_an
                            or existing_record.get("email", ""),
                            "profession": (
                                prof_an
                                if prof_an != "Non renseignée"
                                else existing_record.get(
                                    "profession", "Non renseignée"
                                )
                            ),
                            "biographie": biographie,
                            "stats": {
                                "participation": old_stats.get(
                                    "participation", 0
                                ),
                                "loyaute_groupe": old_stats.get(
                                    "loyaute_groupe", 0
                                ),
                            },
                            "photoUrl": photo_url,
                            "photo": photo_url,
                            "avatar": photo_url,
                            "blason_url": blason_url,
                            "logo_parti_url": logo_parti_url,
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
                            "score_global": existing_record.get(
                                "score_global", 50
                            ),
                            "qualification": existing_record.get(
                                "qualification", "Non évalué"
                            ),
                            "synthese_analyse": existing_record.get(
                                "synthese_analyse", ""
                            ),
                            "votes": existing_record.get("votes", []),
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

        udr_count = sum(1 for d in updated_list if d["groupe"] == "UDR")

        print("✅ Mis à jour avec succès !")
        print(f"📊 Total députés : {len(updated_list)}")
        print(f"🇫🇷 Députés UDR identifiés : {udr_count}")

    except Exception as e:
        print(f"❌ Erreur : {e}")


if __name__ == "__main__":
    fetch_and_update()