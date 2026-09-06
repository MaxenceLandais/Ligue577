let deputesData = [];
let currentSortKey = 'scoreGlobal';
let currentSortDir = 'desc';

function slugifyRegion(str) {
    if (!str) return '';
    let slug = str.toString().toLowerCase()
        .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]/g, "_")
        .replace(/_+/g, "_")
        .replace(/^_+|_+$/g, "");

    if (slug === 'provence_alpes_cote_d_azur') return 'provence_alpes_cote_dazur';
    return slug;
}

const DEPT_TO_REGION = {
    'ain': 'auvergne_rhone_alpes', 'aisne': 'hauts_de_france', 'allier': 'auvergne_rhone_alpes',
    'alpes_de_haute_provence': 'provence_alpes_cote_dazur', 'hautes_alpes': 'provence_alpes_cote_dazur',
    'alpes_maritimes': 'provence_alpes_cote_dazur', 'ardeche': 'auvergne_rhone_alpes', 'ardennes': 'grand_est',
    'ariege': 'occitanie', 'aube': 'grand_est', 'aude': 'occitanie', 'aveyron': 'occitanie',
    'bouches_du_rhone': 'provence_alpes_cote_dazur', 'calvados': 'normandie', 'cantal': 'auvergne_rhone_alpes',
    'charente': 'nouvelle_aquitaine', 'charente_maritime': 'nouvelle_aquitaine', 'cher': 'centre_val_de_loire',
    'correze': 'nouvelle_aquitaine', 'cote_d_or': 'bourgogne_franche_comte', 'cotes_d_armor': 'bretagne',
    'creuse': 'nouvelle_aquitaine', 'dordogne': 'nouvelle_aquitaine', 'doubs': 'bourgogne_franche_comte',
    'drome': 'auvergne_rhone_alpes', 'eure': 'normandie', 'eure_et_loir': 'centre_val_de_loire',
    'finistere': 'bretagne', 'gard': 'occitanie', 'haute_garonne': 'occitanie', 'gers': 'occitanie',
    'gironde': 'nouvelle_aquitaine', 'herault': 'occitanie', 'ille_et_vilaine': 'bretagne',
    'indre': 'centre_val_de_loire', 'indre_et_loire': 'centre_val_de_loire', 'isere': 'auvergne_rhone_alpes',
    'jura': 'bourgogne_franche_comte', 'landes': 'nouvelle_aquitaine', 'loir_et_cher': 'centre_val_de_loire',
    'loire': 'auvergne_rhone_alpes', 'haute_loire': 'auvergne_rhone_alpes', 'loire_atlantique': 'pays_de_la_loire',
    'loiret': 'centre_val_de_loire', 'lot': 'occitanie', 'lot_et_garonne': 'nouvelle_aquitaine',
    'lozere': 'occitanie', 'maine_et_loire': 'pays_de_la_loire', 'manche': 'normandie', 'marne': 'grand_est',
    'haute_marne': 'grand_est', 'mayenne': 'pays_de_la_loire', 'meurthe_et_moselle': 'grand_est',
    'meuse': 'grand_est', 'morbihan': 'bretagne', 'moselle': 'grand_est', 'nievre': 'bourgogne_franche_comte',
    'nord': 'hauts_de_france', 'oise': 'hauts_de_france', 'orne': 'normandie', 'pas_de_calais': 'hauts_de_france',
    'puy_de_dome': 'auvergne_rhone_alpes', 'pyrenees_atlantiques': 'nouvelle_aquitaine',
    'hautes_pyrenees': 'occitanie', 'pyrenees_orientales': 'occitanie', 'bas_rhin': 'grand_est',
    'haut_rhin': 'grand_est', 'rhone': 'auvergne_rhone_alpes', 'haute_saone': 'bourgogne_franche_comte',
    'saone_et_loire': 'bourgogne_franche_comte', 'sarthe': 'pays_de_la_loire', 'savoie': 'auvergne_rhone_alpes',
    'haute_savoie': 'auvergne_rhone_alpes', 'paris': 'ile_de_france', 'seine_maritime': 'normandie',
    'seine_et_marne': 'ile_de_france', 'yvelines': 'ile_de_france', 'deux_sevres': 'nouvelle_aquitaine',
    'somme': 'hauts_de_france', 'tarn': 'occitanie', 'tarn_et_garonne': 'occitanie', 'var': 'provence_alpes_cote_dazur',
    'vaucluse': 'provence_alpes_cote_dazur', 'vendee': 'pays_de_la_loire', 'vienne': 'nouvelle_aquitaine',
    'haute_vienne': 'nouvelle_aquitaine', 'vosges': 'grand_est', 'yonne': 'bourgogne_franche_comte',
    'territoire_de_belfort': 'bourgogne_franche_comte', 'essonne': 'ile_de_france', 'hauts_de_seine': 'ile_de_france',
    'seine_saint_denis': 'ile_de_france', 'val_de_marne': 'ile_de_france', 'val_d_oise': 'ile_de_france',
    'guadeloupe': 'guadeloupe', 'martinique': 'martinique', 'guyane': 'guyane', 'la_reunion': 'la_reunion',
    'mayotte': 'mayotte', 'nouvelle_caledonie': 'nouvelle_caledonie', 'polynesie_francaise': 'polynesie_francaise'
};

const GROUPE_TO_PARTI = {
    'dem': 'dem', 'democrates': 'dem', 'les democrates': 'dem', 'modem': 'dem',
    'dr': 'dr', 'droite republicaine': 'dr', 'lr': 'dr', 'les republicains': 'dr',
    'ecos': 'ecos', 'ecologistes': 'ecos', 'ecologiste et social': 'ecos', 'eelv': 'ecos',
    'epr': 'epr', 'ensemble pour la republique': 'epr',
    'gdr': 'gdr', 'gauche democrate et republicaine': 'gdr', 'pcf': 'gdr',
    'hor': 'hor', 'horizons': 'hor',
    'lfi': 'lfi', 'la france insoumise': 'lfi', 'lfi-nfp': 'lfi',
    'liot': 'liot', 'libertes independance outre-mer et territoires': 'liot',
    're': 're', 'renaissance': 're',
    'rn': 'rn', 'rassemblement national': 'rn',
    'soc': 'soc', 'socialistes': 'soc', 'ps': 'soc', 'socialistes et apparentes': 'soc',
    'udr': 'udr', 'union des droites pour la republique': 'udr'
};

function getRegionSlug(d) {
    if (d.region) return slugifyRegion(d.region);
    if (d.region_nom) return slugifyRegion(d.region_nom);
    const rawDept = (d.circo || d.departement || '').replace(/\s*\([^)]*\)/, '').trim();
    const deptSlug = slugifyRegion(rawDept);
    return DEPT_TO_REGION[deptSlug] || deptSlug;
}

function getPartiSlug(d) {
    const rawParti = (d.groupe || d.parti || '').toString().toLowerCase().trim();
    return GROUPE_TO_PARTI[rawParti] || rawParti;
}

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
    const photoUrl = d.photo || `assets/deputes/${d.id}.jpg`;
    const regionSlug = getRegionSlug(d);
    const partiSlug = getPartiSlug(d);

    return `
        <div class="mini-fut-card">
            <div class="mini-fut-score">${d.scoreGlobal}</div>
            <div class="mini-fut-photo-container">
                <img src="${photoUrl}" alt="${d.nom}" onerror="this.onerror=null; this.src='https://via.placeholder.com/60?text=Depute';">
            </div>
            <div class="mini-fut-bottom">
                <img class="mini-fut-badge" src="assets/regions/${regionSlug}.png" alt="Région" onerror="this.style.visibility='hidden';">
                <span class="mini-fut-leg">17</span>
                <img class="mini-fut-badge" src="assets/partis/${partiSlug}.png" alt="Parti" onerror="this.style.visibility='hidden';">
            </div>
        </div>
    `;
}

function getSortValue(d, key) {
    if (key === 'nom') return d.nom.toLowerCase();
    if (key === 'scoreGlobal' || key === 'bande') return d.scoreGlobal;
    return (d.scores && d.scores[key] !== undefined) ? d.scores[key] : -1;
}

function sortAndRender() {
    deputesData.sort((a, b) => {
        const valA = getSortValue(a, currentSortKey);
        const valB = getSortValue(b, currentSortKey);

        if (typeof valA === 'string') {
            return currentSortDir === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
        }
        return currentSortDir === 'asc' ? valA - valB : valB - valA;
    });

    // Mise à jour visuelle des entêtes
    document.querySelectorAll('th.sortable').forEach(th => {
        th.classList.remove('active', 'asc', 'desc');
        const icon = th.querySelector('.sort-icon');

        if (th.dataset.sort === currentSortKey) {
            th.classList.add('active', currentSortDir);
            if (icon) icon.textContent = currentSortDir === 'asc' ? '▲' : '▼';
        } else {
            if (icon) icon.textContent = '▲▼';
        }
    });

    // Injection des lignes du tableau
    const tbody = document.getElementById('leaderboard');
    if (!tbody) return;
    tbody.innerHTML = '';

    deputesData.forEach((d, index) => {
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
}

function setupSortingEvents() {
    document.querySelectorAll('th.sortable').forEach(th => {
        th.addEventListener('click', () => {
            const sortKey = th.dataset.sort;
            if (currentSortKey === sortKey) {
                currentSortDir = currentSortDir === 'desc' ? 'asc' : 'desc';
            } else {
                currentSortKey = sortKey;
                // Par défaut : ordre alphabétique croissant pour le nom, décroissant pour les scores
                currentSortDir = sortKey === 'nom' ? 'asc' : 'desc';
            }
            sortAndRender();
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    setupSortingEvents();

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

            deputesData = deputes;
            sortAndRender();
        })
        .catch(err => {
            const tbody = document.getElementById('leaderboard');
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="12" style="color:red; font-weight:bold;">Erreur : ${err.message}</td></tr>`;
            }
        });
});