# Observatoire du Libéralisme - MVP

Ce dépôt contient l'architecture complète (Jamstack) pour votre classement des députés.

## Structure
- `index.html` : La page d'accueil (Leaderboard)
- `depute.html` : Le template de profil individuel (avec graphique Radar)
- `assets/` : Contient le CSS et le Javascript
- `data.json` : Votre base de données centralisée.
- `scripts/update_data.py` : Le script Python de calcul des notes.
- `.github/workflows/` : Contient l'automatisation GitHub Actions.

## Comment tester en local sur votre ordinateur ?
Le site utilise `fetch()` pour lire `data.json`. Pour des raisons de sécurité, les navigateurs bloquent cette action si vous ouvrez juste le fichier HTML par un double-clic (erreur CORS). 
**Solution :**
1. Installez l'extension "Live Server" sur VS Code, ou
2. Ouvrez un terminal dans le dossier et tapez : `python -m http.server 8000` puis allez sur http://localhost:8000

## Comment mettre en ligne (Gratuitement)
1. Créez un dépôt sur GitHub et envoyez-y tous ces fichiers.
2. Allez dans les paramètres de votre dépôt GitHub -> **Pages**.
3. Sous "Build and deployment", choisissez "Deploy from a branch" et sélectionnez "main".
4. Votre site sera en ligne en quelques minutes et hébergé gratuitement par GitHub !
5. Le script de mise à jour s'exécutera tout seul tous les lundis grâce à GitHub Actions.
