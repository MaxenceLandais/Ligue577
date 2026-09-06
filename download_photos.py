from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import re
import ssl
import sys
import unicodedata
import urllib.parse
import urllib.request

# Dossiers de destination
DIR_DEPUTES = os.path.join("assets", "deputes")
DIR_REGIONS = os.path.join("assets", "regions")
DIR_PARTIS = os.path.join("assets", "partis")

for folder in [DIR_DEPUTES, DIR_REGIONS, DIR_PARTIS]:
    os.makedirs(folder, exist_ok=True)

HEADERS = {
    "User-Agent": "Ligue577Bot/1.0 (https://github.com/ligue577; contact@ligue577.fr)",
    "Referer": "https://www.assemblee-nationale.fr/",
}

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Noms de fichiers exacts et alternatives sur Wikipédia / Wikimedia Commons
REGION_FILES = {
    "Auvergne-Rhône-Alpes": [
        "Blason_Auvergne-Rhône-Alpes.svg",
        "Blason_fr_Auvergne-Rhône-Alpes.svg",
        "Blason_région_fr_Auvergne-Rhône-Alpes.svg",
    ],
    "Bourgogne-Franche-Comté": [
        "Blason_région_fr_Bourgogne-Franche-Comté.svg",
        "Blason_Bourgogne-Franche-Comté.svg",
        "Blason_fr_Bourgogne-Franche-Comté.svg",
    ],
    "Bretagne": [
        "Blason_fr_Bretagne.svg",
        "Blason_Bretagne.svg",
        "Flag_of_Brittany_(Gwen_ha_du).svg",
    ],
    "Centre-Val de Loire": [
        "Blason_Centre-Val_de_Loire.svg",
        "Blason_Centre-Val-de-Loire.svg",
        "Blason_fr_Centre-Val_de_Loire.svg",
    ],
    "Corse": [
        "Blason_fr_Corse.svg",
        "Blason_Corse.svg",
        "Flag_of_Corsica.svg",
    ],
    "Grand Est": [
        "Blason_du_Grand_Est.svg",
        "Blason_Grand_Est.svg",
        "Blason_du_Grand_Est_en_écu.svg",
    ],
    "Hauts-de-France": [
        "Escutcheon_fr_region_Hauts-de-France.svg",
        "Blason_Hauts-de-France.svg",
        "Blason_région_fr_Hauts-de-France.svg",
    ],
    "Île-de-France": [
        "Blason_fr_Île-de-France.svg",
        "Blason_Île-de-France.svg",
        "Blason_region_fr_Île-de-France.svg",
    ],
    "Normandie": [
        "Blason_region_fr_Normandie.svg",
        "Blason_fr_Normandie.svg",
        "Blason_Normandie.svg",
    ],
    "Nouvelle-Aquitaine": [
        "Blason_Nouvelle-Aquitaine.svg",
        "Blason_région_fr_Nouvelle-Aquitaine.svg",
    ],
    "Occitanie": [
        "Blason_région_fr_Occitanie.svg",
        "Blason_Occitanie.svg",
    ],
    "Pays de la Loire": [
        "Blason_Pays_de_la_Loire.svg",
        "Blason_fr_Pays_de_la_Loire.svg",
        "Drapeau_des_Pays_de_la_Loire.svg",
    ],
    "Provence-Alpes-Côte d'Azur": [
        "Blason_PACA.svg",
        "Blason_Provence-Alpes-Côte_d'Azur.svg",
        "Blason_fr_Provence-Alpes-Côte_d'Azur.svg",
    ],
    "Guadeloupe": [
        "Coat_of_arms_of_Guadeloupe.svg",
        "Armoiries_Guadeloupe.svg",
        "Blason_Guadeloupe.svg",
    ],
    "Martinique": [
        "Coat_of_arms_of_Martinique.svg",
        "Armoiries_Martinique.svg",
        "Drapeau_de_la_Martinique.svg",
    ],
    "Guyane": [
        "Coat_of_Arms_of_French_Guiana.svg",
        "Armoiries_de_la_Guyane.svg",
        "Armoiries_Guyane.svg",
    ],
    "La Réunion": [
        "Armoiries_Réunion.svg",
        "Armoiries_de_La_Réunion.svg",
        "Coat_of_arms_of_Réunion.svg",
    ],
    "Mayotte": [
        "Coat_of_arms_of_Mayotte.svg",
        "Armoiries_de_Mayotte.svg",
        "Armoiries_Mayotte.svg",
    ],
    "Nouvelle-Calédonie": [
        "Emblem_of_New_Caledonia.svg",
        "Emblème_de_la_Nouvelle-Calédonie.svg",
    ],
    "Polynésie française": [
        "Coat_of_arms_of_French_Polynesia.svg",
        "Armoiries_de_la_Polynésie_française.svg",
    ],
}

PARTY_FILES = {
    "RN": [
        "Rassemblement_National.svg",
        "Rassemblement_National_logo_2018.svg",
        "Logo_Rassemblement_National.svg",
    ],
    "EPR": [
        "Logo_Ensemble_Citoyens.svg",
        "Logo_Ensemble_pour_la_République.svg",
        "Ensemble_citoyens_logo.png",
    ],
    "RE": [
        "Renaissance_(parti_politique_français)_logo_2022.svg",
        "Logo_Renaissance_2022.svg",
        "Logo_Ensemble_Citoyens.svg",
    ],
    "LFI": [
        "Logo_La_France_Insoumise.png",
        "Logo_La_France_Insoumise.svg",
        "Logo_France_Insoumise.svg",
    ],
    "SOC": [
        "Parti_socialiste_2021_logo.svg",
        "Logo_Parti_Socialiste_(France)_2021.svg",
        "Logo_PS_2021.svg",
    ],
    "DR": [
        "Les_Républicains_-_logo_(France,_2023).svg",
        "Logo-Les-Républicains-2024.jpg",
        "Logo_Les_Républicains_2024.svg",
        "Logo_Les_Républicains.svg",
    ],
    "EcoS": [
        "Les_Écologistes_logo_2023.svg",
        "Les_ecologistes_logo.svg",
        "Logo_Europe_Écologie_Les_Verts.svg",
    ],
    "DEM": [
        "Mouvement_d'égalité_MoDem.svg",
        "Logo_MoDem_2020.svg",
        "Mouvement_démocrate_(parti_français)_logo.svg",
        "MoDem_logo.svg",
    ],
    "HOR": [
        "Horizons_logo_2021.svg",
        "Logo_Horizons_2021.svg",
        "Logo_Horizons.svg",
    ],
    "UDR": [
        "Logo_UDR_2024.svg",
        "Logo_Union_des_droites_pour_la_République.svg",
    ],
    "GDR": [
        "PCF_logo_2018.svg",
        "Logo_PCF_2018.svg",
        "Logo_Parti_communiste_français.svg",
    ],
    "LIOT": [
        "Logo_LIOT_2022.svg",
        "Logo_LIOT.svg",
        "Logo_groupe_LIOT.svg",
    ],
}


def slugify(text):
    text = unicodedata.normalize("NFD", str(text))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn").lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "_", text).strip("_")


def fetch_wiki_image_url(file_names, query_hint="", width=250):
    """
    Interroge l'API Wikipédia/Commons avec gestion des redirections,
    recherche automatique et fallback d'images d'articles.
    """
    if isinstance(file_names, str):
        candidates = [file_names]
    else:
        candidates = list(file_names)

    apis = [
        "https://fr.wikipedia.org/w/api.php",
        "https://commons.wikimedia.org/w/api.php",
    ]

    # 1. Test direct sur la liste de noms de fichiers candidats
    for file_name in candidates:
        file_title = (
            file_name if file_name.startswith("File:") else f"File:{file_name}"
        )
        for api_base in apis:
            params = urllib.parse.urlencode({
                "action": "query",
                "titles": file_title,
                "prop": "imageinfo",
                "iiprop": "url",
                "iiurlwidth": width,
                "redirects": "1",
                "format": "json",
            })
            url = f"{api_base}?{params}"
            req = urllib.request.Request(url, headers=HEADERS)
            try:
                with urllib.request.urlopen(
                    req, context=ssl_context, timeout=5
                ) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    pages = data.get("query", {}).get("pages", {})
                    for page_id, page_data in pages.items():
                        if (
                            page_id != "-1"
                            and "imageinfo" in page_data
                            and page_data["imageinfo"]
                        ):
                            info = page_data["imageinfo"][0]
                            return info.get("thumburl") or info.get("url")
            except Exception:
                continue

    # 2. Recherche MediaWiki Fallback via l'API Search dans le namespace 6 (Fichiers)
    if query_hint:
        for api_base in apis:
            params = urllib.parse.urlencode({
                "action": "query",
                "list": "search",
                "srnamespace": "6",
                "srsearch": query_hint,
                "format": "json",
            })
            url = f"{api_base}?{params}"
            req = urllib.request.Request(url, headers=HEADERS)
            try:
                with urllib.request.urlopen(
                    req, context=ssl_context, timeout=5
                ) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    search_results = data.get("query", {}).get("search", [])
                    for res in search_results[:3]:
                        found_title = res.get("title")
                        if found_title:
                            img_url = fetch_wiki_image_url(
                                [found_title], width=width
                            )
                            if img_url:
                                return img_url
            except Exception:
                continue

    # 3. Fallback sur l'image principale de la page Wikipédia (PageImages)
    if query_hint:
        params = urllib.parse.urlencode({
            "action": "query",
            "titles": query_hint,
            "prop": "pageimages",
            "piprop": "thumbnail|original",
            "pithumbsize": width,
            "redirects": "1",
            "format": "json",
        })
        url = f"https://fr.wikipedia.org/w/api.php?{params}"
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(
                req, context=ssl_context, timeout=5
            ) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pages = data.get("query", {}).get("pages", {})
                for page_id, page_data in pages.items():
                    if page_id != "-1":
                        if "thumbnail" in page_data:
                            return page_data["thumbnail"]["source"]
                        if "original" in page_data:
                            return page_data["original"]["source"]
        except Exception:
            pass

    return None


def download_file(url, target_path, min_bytes=500):
    if os.path.exists(target_path) and os.path.getsize(target_path) > min_bytes:
        print(f"⏩ Déjà présent : {target_path}")
        return True
    if not url:
        return False
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(
            req, context=ssl_context, timeout=10
        ) as resp:
            data = resp.read()
            if len(data) > min_bytes and not data.startswith(b"<!DOCTYPE"):
                with open(target_path, "wb") as out:
                    out.write(data)
                print(f"✅ Enregistré : {target_path}")
                return True
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement : {e}")
    return False


# --- 1. Téléchargement des Blasons ---
print("🛡️ Téléchargement des blasons de régions...")
for region_name, file_candidates in REGION_FILES.items():
    target_path = os.path.join(DIR_REGIONS, f"{slugify(region_name)}.png")
    if not os.path.exists(target_path):
        img_url = fetch_wiki_image_url(
            file_candidates, query_hint=f"Blason {region_name}", width=250
        )
        download_file(img_url, target_path)

# --- 2. Téléchargement des Logos de Partis ---
print("\n🏛️ Téléchargement des logos de partis...")
for parti_code, file_candidates in PARTY_FILES.items():
    target_path = os.path.join(DIR_PARTIS, f"{slugify(parti_code)}.png")
    if not os.path.exists(target_path):
        img_url = fetch_wiki_image_url(
            file_candidates, query_hint=f"Logo {parti_code}", width=250
        )
        download_file(img_url, target_path)


# --- 3. Députés ---
def get_tokens(text):
    text = unicodedata.normalize("NFD", str(text))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn").lower()
    text = re.sub(r"\b(mme|m|monsieur|madame)\b", "", text)
    tokens = [t for t in re.split(r"[^a-z0-9]+", text) if t]
    return frozenset(tokens)


print("\n📋 Chargement de data.json...")
deputes = []
if os.path.exists("data.json"):
    with open("data.json", "r", encoding="utf-8") as f:
        deputes = json.load(f)
    print(f"✅ {len(deputes)} députés chargés.")

print("🔍 Connexion à l'annuaire de l'Assemblée nationale...")
an_token_mapping = {}

try:
    url_annuaire = (
        "https://www2.assemblee-nationale.fr/deputes/liste/alphabetique"
    )
    req = urllib.request.Request(url_annuaire, headers=HEADERS)
    with urllib.request.urlopen(req, context=ssl_context, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    matches = re.findall(
        r'href=["\'](?:/deputes/fiche/OMC_|/dyn/deputes/)(PA\d+)["\'][^>]*>\s*([^<]+)</a>',
        html,
        re.IGNORECASE,
    )

    for pa_id, raw_name in matches:
        tokens = get_tokens(raw_name)
        if tokens:
            an_token_mapping[tokens] = pa_id.upper()

    print(
        f"✅ {len(an_token_mapping)} députés identifiés sur le site officiel.\n"
    )

except Exception as e:
    print(f"❌ Erreur lors de l'accès à l'annuaire : {e}")


def download_one_photo(d):
    dep_id = str(d.get("id", "")).strip()
    if not dep_id:
        return

    nom = d.get("nom", dep_id)
    file_path = os.path.join(DIR_DEPUTES, f"{dep_id}.jpg")

    if os.path.exists(file_path) and os.path.getsize(file_path) > 1000:
        return

    pa_id = None
    num_match = re.search(r"PA\d+|\d+", dep_id, re.IGNORECASE)
    if num_match and len(num_match.group(0)) > 4:
        found_num = num_match.group(0).upper()
        pa_id = found_num if found_num.startswith("PA") else f"PA{found_num}"

    if not pa_id:
        tokens_nom = get_tokens(nom)
        tokens_id = get_tokens(dep_id)
        pa_id = an_token_mapping.get(tokens_nom) or an_token_mapping.get(
            tokens_id
        )

        if not pa_id:
            for an_tokens, matched_pa in an_token_mapping.items():
                if tokens_nom.issubset(an_tokens) or an_tokens.issubset(
                    tokens_nom
                ):
                    pa_id = matched_pa
                    break

    if not pa_id:
        return

    num_only = pa_id.replace("PA", "")
    candidate_urls = [
        f"https://www.assemblee-nationale.fr/dyn/static/tribun/17/photos/{num_only}.jpg",
        f"https://www.assemblee-nationale.fr/dyn/static/tribun/17/photos/{pa_id}.jpg",
        f"https://www2.assemblee-nationale.fr/static/tribun/17/photos/{pa_id}.jpg",
        f"https://datan.fr/assets/imgs/deputes/depute_{pa_id.lower()}.png",
    ]

    for photo_url in candidate_urls:
        if download_file(photo_url, file_path, min_bytes=1000):
            print(f"📸 Photo enregistrée : {nom} ({pa_id})")
            return


if deputes:
    print("📥 Téléchargement parallèle de toutes les photos de députés...")
    executor = ThreadPoolExecutor(max_workers=10)
    try:
        futures = [executor.submit(download_one_photo, d) for d in deputes]
        for future in as_completed(futures):
            future.result()
    except KeyboardInterrupt:
        print("\n🛑 Interruption.")
        executor.shutdown(wait=False, cancel_futures=True)
        sys.exit(0)

print("\n🎉 Téléchargement terminé avec succès !")