function getBande(score) {
    if (score >= 91) return { label: "Très libéral", class: "bande-tres-liberal" };
    if (score >= 81) return { label: "Libéral", class: "bande-liberal" };
    if (score >= 71) return { label: "Plutôt libéral", class: "bande-plutot" };
    if (score >= 61) return { label: "Modérément libéral", class: "bande-modere" };
    if (score >= 51) return { label: "Peu libéral", class: "bande-peu" };
    return { label: "Dirigiste", class: "bande-dirigiste" };
}

function getScoreClass(val) {
    if (val === null || val === undefined || val === '—') return '';
    const score = Number(val);
    if (isNaN(score)) return '';
    if (score >= 91) return 'score-tres-liberal';
    if (score >= 81) return 'score-liberal';
    if (score >= 71) return 'score-plutot';
    if (score >= 61) return 'score-modere';
    if (score >= 51) return 'score-peu';
    return 'score-dirigiste';
}

function renderScorePill(val) {
    if (val === null || val === undefined || val === '—') return '—';
    const scoreClass = getScoreClass(val);
    return `<span class="score-pill ${scoreClass}">${val}</span>`;
}

function renderMiniFutCard(d) {
    const photoUrl = d.photo || d.avatar || `assets/photos/${d.id}.jpg`;
    const regionLogo = d.logo_region || d.region_logo || `assets/logos/regions/${d.region_code || 'france'}.png`;
    const partiLogo = d.logo_parti || d.parti_logo || `assets/logos/partis/${(d.groupe || 'udr').toLowerCase()}.png`;

    // Placeholders SVG si les fichiers locaux n'existent pas encore
    const fallbackRegion = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230f172a'%3E%3Cpath d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z'/%3E%3C/svg%3E";
    const fallbackParti = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230f172a'%3E%3Cpath d='M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z'/%3E%3C/svg%3E";

    return `
        <div class="mini-fut-card">
            <div class="mini-fut-score">${d.scoreGlobal}</div>
            <div class="mini-fut-photo-container">
                <img src="${photoUrl}" alt="${d.nom}" onerror="this.onerror=null; this.src='https://via.placeholder.com/80?text=Depute';">
            </div>
            <div class="mini-fut-bottom">
                <img class="mini-fut-badge" src="${regionLogo}" alt="Région" onerror="this.onerror=null; this.src='${fallbackRegion}';">
                <span class="mini-fut-leg">17</span>
                <img class="mini-fut-badge" src="${partiLogo}" alt="Parti" onerror="this.onerror=null; this.src='${fallbackParti}';">
            </div>
        </div>
    `;
}

document.addEventListener('DOMContentLoaded', () => {
    fetch('./data.json?t=' + Date.now())
        .then(res => {
            if (!res.ok) throw new Error("Impossible de lire data.json");
            return res.json();
        })
        .then(deputes => {
            deputes.forEach(d => {
                const vals = Object.values(d.scores || {});
                d.scoreGlobal = d.score_global !== undefined
                    ? d.score_global
                    : (vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0);
                d.bande = getBande(d.scoreGlobal);
            });

            deputes.sort((a, b) => b.scoreGlobal - a.scoreGlobal);

            const tbody = document.getElementById('leaderboard');
            if (!tbody) return;
            tbody.innerHTML = '';

            deputes.forEach((d, index) => {
                const scores = d.scores || {};
                const tr = document.createElement('tr');
                tr.className = 'clickable-row';
                tr.onclick = () => window.location.href = `depute.html?id=${d.id}`;

                tr.innerHTML = `
                    <td class="col-rang">#${index + 1}</td>
                    <td class="col-carte">${renderMiniFutCard(d)}</td>
                    <td class="col-nom">
                        <a href="depute.html?id=${d.id}" class="depute-link" onclick="event.stopPropagation();">${d.nom}</a>
                    </td>
                    <td class="col-circo">${d.circo || '—'}</td>
                    <td class="col-score-global">${renderScorePill(d.scoreGlobal)}</td>
                    <td class="col-pillar">${renderScorePill(scores.FIS)}</td>
                    <td class="col-pillar">${renderScorePill(scores.PRO)}</td>
                    <td class="col-pillar">${renderScorePill(scores.ETA)}</td>
                    <td class="col-pillar">${renderScorePill(scores.LIB)}</td>
                    <td class="col-pillar">${renderScorePill(scores.REG)}</td>
                    <td class="col-pillar">${renderScorePill(scores.OUV)}</td>
                    <td><span class="badge ${d.bande.class}">${d.bande.label}</span></td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(err => {
            const tbody = document.getElementById('leaderboard');
            if (tbody) {
                tbody.innerHTML = `
                    <tr><td colspan="12" style="color:red; font-weight:bold;">Erreur : ${err.message}</td></tr>
                `;
            }
        });
});