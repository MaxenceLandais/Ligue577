function getBande(score) {
    if (score >= 80) return { label: "Libéral", class: "bande-liberal" };
    if (score >= 70) return { label: "Plutôt libéral", class: "bande-plutot" };
    if (score >= 60) return { label: "Modérément libéral", class: "bande-modere" };
    if (score >= 50) return { label: "Peu libéral", class: "bande-peu" };
    return { label: "Dirigiste", class: "bande-dirigiste" };
}

function getScoreClass(val) {
    if (val === null || val === undefined || val === '—') return '';
    const score = Number(val);
    if (isNaN(score)) return '';
    if (score >= 80) return 'score-liberal';
    if (score >= 70) return 'score-plutot';
    if (score >= 60) return 'score-modere';
    if (score >= 50) return 'score-peu';
    return 'score-dirigiste';
}

function renderScorePill(val) {
    if (val === null || val === undefined || val === '—') return '—';
    const scoreClass = getScoreClass(val);
    return `<span class="score-pill ${scoreClass}">${val}</span>`;
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
                    <tr><td colspan="11" style="color:red; font-weight:bold;">Erreur : ${err.message}</td></tr>
                `;
            }
        });
});