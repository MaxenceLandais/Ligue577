// Attribue la bande en fonction du score global
function getBande(score) {
  if (score >= 80) return "Libéral";
  if (score >= 70) return "Plutôt libéral";
  if (score >= 60) return "Modérément libéral";
  if (score >= 50) return "Peu libéral";
  return "Dirigiste";
}

// Calcule la moyenne des 6 piliers
function calculerScoreGlobal(scores) {
  const piliers = Object.values(scores);
  const somme = piliers.reduce((acc, val) => acc + val, 0);
  return Math.round(somme / piliers.length);
}

// Chargement des données
fetch('deputes.json')
  .then(response => response.json())
  .then(deputes => {
    // Calcul des scores et ajout de la bande
    deputes.forEach(d => {
      d.scoreGlobal = calculerScoreGlobal(d.scores);
      d.bande = getBande(d.scoreGlobal);
    });

    // Tri décroissant selon le score global
    deputes.sort((a, b) => b.scoreGlobal - a.scoreGlobal);

    // 1. Remplissage du tableau
    const tbody = document.querySelector('#tableau-classement tbody');
    deputes.forEach((d, index) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${index + 1}</strong></td>
        <td><a href="#fiche-${d.id}">${d.nom}</a></td>
        <td>${d.circo}</td>
        <td><strong>${d.scoreGlobal}</strong></td>
        <td>${d.bande}</td>
      `;
      tbody.appendChild(tr);
    });

    // 2. Remplissage des fiches détaillées
    const fichesContainer = document.getElementById('fiches-container');
    deputes.forEach(d => {
      const fiche = document.createElement('article');
      fiche.id = `fiche-${d.id}`;
      fiche.className = 'fiche-depute';
      fiche.innerHTML = `
        <h3>${d.nom} (${d.circo})</h3>
        <p><strong>Score global :</strong> ${d.scoreGlobal} / 100 — <em>${d.bande}</em></p>
        <p>${d.bio}</p>
        <h4>Notes par pilier :</h4>
        <ul>
          <li><strong>FIS (Fiscalité) :</strong> ${d.scores.FIS}</li>
          <li><strong>ÉTA (Périmètre de l'État) :</strong> ${d.scores.ETA}</li>
          <li><strong>RÉG (Régulation) :</strong> ${d.scores.REG}</li>
          <li><strong>PRO (Propriété) :</strong> ${d.scores.PRO}</li>
          <li><strong>LIB (Libertés) :</strong> ${d.scores.LIB}</li>
          <li><strong>OUV (Ouverture) :</strong> ${d.scores.OUV}</li>
        </ul>
        <hr>
      `;
      fichesContainer.appendChild(fiche);
    });
  });