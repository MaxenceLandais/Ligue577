import json
import re
import subprocess
import sys
import time
import unicodedata
from playwright.sync_api import sync_playwright, Error as PlaywrightError


def ensure_chromium_installed():
    print("⚙️ Téléchargement automatique du navigateur Chromium...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)


def load_json_file(filepath, default_value):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_value


def save_json_file(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def clean_alpha_only(text: str) -> str:
    """Supprime les accents et ne garde QUE les lettres (pas de tirets, espaces ou apostrophes)."""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-zA-Z]', '', text).lower()


def build_datan_slug(full_name: str) -> str:
    """
    Génère le slug Datan strict :
    - Prénom tout attaché
    - Nom tout attaché
    - Un seul tiret séparateur
    """
    parts = full_name.strip().split(maxsplit=1)
    if not parts:
        return ""

    prenom = parts[0]
    nom_famille = parts[1] if len(parts) > 1 else ""

    prenom_slug = clean_alpha_only(prenom)
    nom_slug = clean_alpha_only(nom_famille)

    if nom_slug:
        return f"depute_{prenom_slug}-{nom_slug}"
    return f"depute_{prenom_slug}"


def fix_datan_url(raw_url: str, full_name: str) -> str:
    if not raw_url:
        return ""
    # Conserve la circonscription (ex: https://datan.fr/deputes/alpes-maritimes-06)
    match = re.match(r"^(https?://datan\.fr/deputes/[^/]+)", raw_url.strip())
    if not match:
        return raw_url

    circo_base = match.group(1)
    correct_slug = build_datan_slug(full_name)
    return f"{circo_base}/{correct_slug}"


def scrape_depute_page(page, datan_url):
    base_url = datan_url.split("?")[0].rstrip("/")
    votes_url = base_url if base_url.endswith("/votes") else f"{base_url}/votes"

    print(f"  🌐 URL : {votes_url}")
    page.goto(votes_url, wait_until="domcontentloaded")

    try:
        page.wait_for_selector("text=votes", timeout=6000)
    except Exception:
        pass

    # Cookies
    try:
        cookie_btn = page.query_selector("button:has-text('Accepter'), #axeptio_btn_accept")
        if cookie_btn and cookie_btn.is_visible():
            cookie_btn.click()
            time.sleep(1)
    except Exception:
        pass

    # "Voir plus"
    while True:
        try:
            btn_more = page.query_selector("button:has-text('Voir plus'), a:has-text('Voir plus')")
            if btn_more and btn_more.is_visible():
                btn_more.click()
                time.sleep(1.2)
            else:
                break
        except Exception:
            break

    # Extraction JS
    js_script = r'''() => {
        const results = [];
        const elements = Array.from(document.querySelectorAll('div, a, article'));

        const cardNodes = elements.filter(el => {
            const text = el.innerText || '';
            const hasVote = text.includes('POUR') || text.includes('CONTRE') || text.includes('ABSTENTION');
            const hasDate = /\d{1,2}\s+[a-zàâäéèêëîïôöùûüç\.]+\s+\d{4}/i.test(text);
            return hasVote && hasDate && el.children.length >= 2 && el.children.length <= 10;
        });

        const specificCards = cardNodes.filter(c1 => 
            !cardNodes.some(c2 => c1 !== c2 && c1.contains(c2))
        );

        const seen = new Set();

        for (const card of specificCards) {
            const fullText = card.innerText.trim();
            if (seen.has(fullText)) continue;
            seen.add(fullText);

            const lines = fullText.split('\n').map(l => l.trim()).filter(Boolean);

            let position = 'Non précisé';
            if (fullText.includes('POUR')) position = 'POUR';
            else if (fullText.includes('CONTRE')) position = 'CONTRE';
            else if (fullText.includes('ABSTENTION')) position = 'ABSTENTION';

            const dateMatch = fullText.match(/\d{1,2}\s+[a-zàâäéèêëîïôöùûüç\.]+\s+\d{4}/i);
            const dateStr = dateMatch ? dateMatch[0] : '';

            const contentLines = lines.filter(line => 
                !['POUR', 'CONTRE', 'ABSTENTION'].includes(line.toUpperCase()) &&
                !/\d{1,2}\s+[a-zàâäéèêëîïôöùûüç\.]+\s+\d{4}/i.test(line)
            );

            const title = contentLines[0] || 'Titre inconnu';
            const description = contentLines.slice(1).join(' - ') || '';

            results.push({
                titre: title,
                position: position,
                date: dateStr,
                description: description,
                texte_brut: fullText
            });
        }

        return results;
    }'''

    return page.evaluate(js_script)


def scrape_all_udr_votes():
    deputes = load_json_file("data.json", [])
    udr_deputes = [d for d in deputes if d.get("groupe", "").upper() == "UDR"]

    if not udr_deputes:
        print("❌ Aucun député UDR trouvé dans data.json !")
        return

    print(f"🚀 Début du scraping pour {len(udr_deputes)} députés UDR...\n")
    all_votes = load_json_file("votes.json", {})

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except PlaywrightError as e:
            if "Executable doesn't exist" in str(e) or "playwright install" in str(e):
                ensure_chromium_installed()
                browser = p.chromium.launch(headless=True)
            else:
                raise e

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        for index, depute in enumerate(udr_deputes, 1):
            depute_id = depute.get("id")
            nom = depute.get("nom", depute_id)
            raw_url = depute.get("datanUrl", "")

            # Correction de l'URL selon la règle stricte Datan
            fixed_url = fix_datan_url(raw_url, nom)
            if raw_url != fixed_url:
                print(f"🛠️ URL corrigée : {raw_url} ➔ {fixed_url}")
                depute["datanUrl"] = fixed_url

            print(f"[{index}/{len(udr_deputes)}] Scraping : {nom} ({depute_id})")

            if not fixed_url:
                print(f"  ⚠️ URL Datan manquante pour {nom}, ignoré.")
                continue

            page = context.new_page()
            try:
                votes_list = scrape_depute_page(page, fixed_url)
                all_votes[depute_id] = votes_list

                # Sauvegarde en direct dans les JSON
                save_json_file("votes.json", all_votes)
                save_json_file("data.json", deputes)
                print(f"  ✅ {len(votes_list)} votes enregistrés pour {nom}\n")
            except Exception as e:
                print(f"  ❌ Erreur pour {nom} : {e}\n")
            finally:
                page.close()

            time.sleep(1)

        browser.close()

    print("🎉 Scraping terminé ! 'data.json' et 'votes.json' sont à jour.")


if __name__ == "__main__":
    scrape_all_udr_votes()