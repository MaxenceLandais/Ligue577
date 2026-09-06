from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import re
import ssl
import sys
import unicodedata
import urllib.request

# Dossier de destination
os.makedirs("assets/deputes", exist_ok=True)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.assemblee-nationale.fr/",
}

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def get_tokens(text):
    """Découpe un nom en mots nettoyés (sans accent, minuscules, sans civilité, insensible à l'ordre)."""
    text = unicodedata.normalize("NFD", str(text))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn").lower()
    text = re.sub(r"\b(mme|m|monsieur|madame)\b", "", text)
    tokens = [t for t in re.split(r"[^a-z0-9]+", text) if t]
    return frozenset(tokens)


# 1. Chargement du fichier data.json
with open("data.json", "r", encoding="utf-8") as f:
    deputes = json.load(f)

print(f"📋 {len(deputes)} députés chargés depuis data.json.")

# 2. Récupération de l'annuaire officiel de l'Assemblée nationale
print("🔍 Connexion à l'annuaire de l'Assemblée nationale...")
an_token_mapping = {}

try:
    url_annuaire = (
        "https://www2.assemblee-nationale.fr/deputes/liste/alphabetique"
    )
    req = urllib.request.Request(url_annuaire, headers=headers)
    with urllib.request.urlopen(
        req, context=ssl_context, timeout=10
    ) as resp:
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
    file_path = f"assets/deputes/{dep_id}.jpg"

    # Ignorer si la photo est déjà sur le disque
    if os.path.exists(file_path) and os.path.getsize(file_path) > 1000:
        return

    pa_id = None

    # A. Si l'ID contient déjà un matricule PA numérique
    num_match = re.search(r"PA\d+|\d+", dep_id, re.IGNORECASE)
    if num_match and len(num_match.group(0)) > 4:
        found_num = num_match.group(0).upper()
        pa_id = found_num if found_num.startswith("PA") else f"PA{found_num}"

    # B. Matching insensible à l'ordre Nom/Prénom
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
        print(f"❌ Matricule introuvable pour : {nom}")
        return

    num_only = pa_id.replace("PA", "")

    # URLs candidates
    candidate_urls = [
        f"https://www.assemblee-nationale.fr/dyn/static/tribun/17/photos/{num_only}.jpg",
        f"https://www.assemblee-nationale.fr/dyn/static/tribun/17/photos/{pa_id}.jpg",
        f"https://www2.assemblee-nationale.fr/static/tribun/17/photos/{pa_id}.jpg",
        f"https://datan.fr/assets/imgs/deputes/depute_{pa_id.lower()}.png",
    ]

    for photo_url in candidate_urls:
        try:
            req = urllib.request.Request(photo_url, headers=headers)
            with (
                urllib.request.urlopen(
                    req, context=ssl_context, timeout=5
                ) as resp,
                open(file_path, "wb") as out,
            ):
                data = resp.read()
                if len(data) > 1000 and not data.startswith(b"<!DOCTYPE"):
                    out.write(data)
                    print(f"✅ Photo enregistrée : {nom} ({pa_id})")
                    return
        except Exception:
            continue

    print(f"❌ Échec de téléchargement : {nom} ({pa_id})")


print("📥 Téléchargement parallèle de toutes les photos...")

executor = ThreadPoolExecutor(max_workers=10)
try:
    futures = [executor.submit(download_one_photo, d) for d in deputes]
    for future in as_completed(futures):
        future.result()
except KeyboardInterrupt:
    print("\n🛑 Interruption par l'utilisateur (Ctrl+C).")
    executor.shutdown(wait=False, cancel_futures=True)
    sys.exit(0)

print("\n🎉 Téléchargement terminé !")