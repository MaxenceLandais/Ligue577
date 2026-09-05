// Utilitaires
function getBandeClass(bande) {
    if (bande === "Libéral") return "bande-liberal";
    if (bande === "Plutôt libéral") return "bande-plutot";
    if (bande === "Modérément libéral") return "bande-modere";
    if (bande === "Peu libéral") return "bande-peu";
    return "bande-dirigiste";
}

// Fonction principale pour charger la data
async function loadData() {
    try {
        // En production (GitHub Pages), fetch('data.json') fonctionne parfaitement.
        const response = await fetch('data.json');
        const data = await response.json();
        
        // Routage basique
        if (document.getElementById('leaderboardBody')) {
            renderLeaderboard(data);
        } else if (document.getElementById('profileContainer')) {
            renderProfile(data);
        }
    } catch (error) {
        console.error("Erreur de chargement des données:", error);
        document.body.innerHTML += `<div style="color:red; text-align:center; padding: 2rem;">Erreur de chargement de la base de données. Si vous êtes en local, utilisez un serveur (ex: Live Server).</div>`;
    }
}

// Rendu de la page Accueil
function renderLeaderboard(data) {
    document.getElementById('lastUpdate').innerText = `Dernière mise à jour : ${data.metadata.last_updated}`;
    const tbody = document.getElementById('leaderboardBody');
    tbody.innerHTML = '';

    // Trier par score décroissant
    const deputies = data.deputies.sort((a, b) => b.score_total - a.score_total);

    deputies.forEach((dep, index) => {
        const row = `<tr>
            <td><strong>#${index + 1}</strong></td>
            <td><strong>${dep.name}</strong></td>
            <td>${dep.department}</td>
            <td><strong>${dep.score_total}</strong></td>
            <td><span class="badge ${getBandeClass(dep.bande)}">${dep.bande}</span></td>
            <td><a href="depute.html?id=${dep.id}" class="btn">Analyser</a></td>
        </tr>`;
        tbody.innerHTML += row;
    });
}

// Rendu de la page Profil
function renderProfile(data) {
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');
    const deputy = data.deputies.find(d => d.id === id);

    if (!deputy) {
        document.getElementById('loadingMsg').innerText = "Député introuvable.";
        return;
    }

    document.getElementById('loadingMsg').style.display = 'none';
    document.getElementById('profileContainer').style.display = 'block';

    // Infos de base
    document.getElementById('depName').innerText = deputy.name;
    document.getElementById('depDept').innerText = `${deputy.group} - ${deputy.department}`;
    document.getElementById('depScore').innerText = deputy.score_total;
    document.getElementById('depBio').innerText = deputy.bio;
    
    const badgeEl = document.getElementById('depBande');
    badgeEl.innerText = deputy.bande;
    badgeEl.className = `badge ${getBandeClass(deputy.bande)}`;

    // Historique
    const tbody = document.getElementById('historyBody');
    if(deputy.recent_actions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3">Aucun vote majeur récent analysé.</td></tr>';
    } else {
        deputy.recent_actions.forEach(act => {
            tbody.innerHTML += `<tr>
                <td><small>${act.date}</small></td>
                <td><strong>${act.type} :</strong> ${act.description}</td>
                <td><span style="color:#2563eb; font-weight:bold;">${act.impact}</span></td>
            </tr>`;
        });
    }

    // Graphique Radar Chart.js
    const ctx = document.getElementById('radarChart').getContext('2d');
    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: [
                'Fiscalité (FIS)', 
                'Périmètre État (ÉTA)', 
                'Régulation (RÉG)', 
                'Propriété (PRO)', 
                'Libertés (LIB)', 
                'Ouverture (OUV)'
            ],
            datasets: [{
                label: `Score de ${deputy.name} (sur 20)`,
                data: [
                    deputy.scores_detail.FIS,
                    deputy.scores_detail.ETA,
                    deputy.scores_detail.REG,
                    deputy.scores_detail.PRO,
                    deputy.scores_detail.LIB,
                    deputy.scores_detail.OUV
                ],
                backgroundColor: 'rgba(15, 23, 42, 0.2)', // primary color transp
                borderColor: 'rgba(15, 23, 42, 1)',
                pointBackgroundColor: 'rgba(15, 23, 42, 1)',
                borderWidth: 2
            }]
        },
        options: {
            scales: {
                r: {
                    angleLines: { display: true },
                    suggestedMin: 0,
                    suggestedMax: 20,
                    ticks: { stepSize: 5 }
                }
            },
            plugins: { legend: { display: false } },
            maintainAspectRatio: false
        }
    });
}

// Initialisation
window.onload = loadData;
