function getBande(score) {
    if (score >= 80) return { label: "Libéral", class: "bande-liberal" };
    if (score >= 70) return { label: "Plutôt libéral", class: "bande-plutot" };
    if (score >= 60) return { label: "Modérément libéral", class: "bande-modere" };
    if (score >= 50) return { label: "Peu libéral", class: "bande-peu" };
    return { label: "Dirigiste", class: "bande-dirigiste" };
}

document.addEventListener('DOMContentLoaded', () => {
    const leaderboardBody = document.getElementById('leaderboardBody');
    const lastUpdate = document.getElementById('lastUpdate');

    if (lastUpdate) {
        const today = new Date();
        lastUpdate.textContent = `Dernière mise à jour : ${today.toISOString().split('T')[0]}`;
    }

    // Chargement dynamique de data.json avec contournement du cache
    fetch('data.json?t=' + new Date().getTime())
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP ${response.status} : fichier data.json introuvable`);
            }
            return response.json();
        })
        .then(deputes => {
            deputes.forEach(d => {
                const scores = Object.values(d.scores || {});
                d.scoreGlobal = scores.length > 0 
                    ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) 
                    : 0;
                d.bandeInfo = getBande(d.scoreGlobal);
            });

            deputes.sort((a, b) => b.scoreGlobal - a.scoreGlobal);

            if (leaderboardBody) {
                leaderboardBody.innerHTML = '';

                deputes.forEach((d, index) => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td><strong>#${index + 1}</strong></td>
                        <td><strong>${d.nom}</strong></td>
                        <td>${d.circo}</td>
                        <td><strong>${d.scoreGlobal}</strong> / 100</td>
                        <td><span class="badge ${d.bandeInfo.class}">${d.bandeInfo.label}</span></td>
                        <td><a href="depute.html?id=${d.id}" class="btn-detail" style="text-decoration: underline; color: #2563eb;">Voir la fiche</a></td>
                    `;
                    leaderboardBody.appendChild(row);
                });
            }
        })
        .catch(error => {
            console.error('Erreur :', error);
            if (leaderboardBody) {
                leaderboardBody.innerHTML = `
                    <tr>
                        <td colspan="6" style="color: #ef4444; text-align: center; padding: 20px;">
                            <strong>Erreur :</strong> ${error.message}<br>
                            <small style="color: #64748b;">Vérifiez que le fichier <code>data.json</code> est bien présent à la racine sur GitHub.</small>
                        </td>
                    </tr>
                `;
            }
        });
});