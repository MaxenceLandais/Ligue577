const PILLARS_MAP = {
    FIS: { label: "Santé Fiscale & Impôts", desc: "Modération fiscale et attractivité" },
    ETA: { label: "Taille de l'État & Dépenses", desc: "Maîtrise des dépenses publiques" },
    REG: { label: "Fardeau Réglementaire", desc: "Simplification et liberté des affaires" },
    PRO: { label: "Droit de Propriété", desc: "Protection du capital et du patrimoine" },
    LIB: { label: "Liberté du Travail", desc: "Flexibilité et liberté d'embauche" },
    OUV: { label: "Ouverture des Marchés", desc: "Libre-échange et concurrence" }
};

const REGION_FLAGS = {
    "Occitanie": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Flag_of_Occitanie.svg/1200px-Flag_of_Occitanie.svg.png",
    "Provence-Alpes-Côte d'Azur": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Flag_of_Provence-Alpes-C%C3%B4te_d%27Azur.svg/1200px-Flag_of_Provence-Alpes-C%C3%B4te_d%27Azur.svg.png"
};

const PARTY_LOGOS = {
    "UDR": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Logo_Union_des_droites_pour_la_R%C3%A9publique_2024.svg/250px-Logo_Union_des_droites_pour_la_R%C3%A9publique_2024.svg.png"
};

const SOCIAL_NAMES = {
    x: "X (Twitter)",
    facebook: "Facebook",
    linkedin: "LinkedIn",
    instagram: "Instagram"
};

function slugifyAsset(text) {
    if (!text) return '';
    return text
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/[^\w\s-]/g, "")
        .replace(/[\s_-]+/g, "_")
        .replace(/^_+|_+$/g, "");
}

function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

function calculateAge(birthDateStr) {
    if (!birthDateStr) return null;
    let birthDate;
    if (birthDateStr.includes('-')) {
        const parts = birthDateStr.split('-');
        birthDate = parts[0].length === 4
            ? new Date(birthDateStr)
            : new Date(`${parts[2]}-${parts[1]}-${parts[0]}`);
    } else if (birthDateStr.includes('/')) {
        const parts = birthDateStr.split('/');
        birthDate = new Date(`${parts[2]}-${parts[1]}-${parts[0]}`);
    } else {
        birthDate = new Date(birthDateStr);
    }

    if (isNaN(birthDate.getTime())) return null;

    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    return age;
}

function getBande(score) {
    if (score >= 80) return { label: "Libéral", class: "bande-liberal", color: "#16a34a" };
    if (score >= 70) return { label: "Plutôt libéral", class: "bande-plutot", color: "#0284c7" };
    if (score >= 60) return { label: "Modérément libéral", class: "bande-modere", color: "#ca8a04" };
    if (score >= 50) return { label: "Peu libéral", class: "bande-peu", color: "#ea580c" };
    return { label: "Dirigiste", class: "bande-dirigiste", color: "#dc2626" };
}

function getFutCardThemeClass(score) {
    if (score <= 50) return 'fut-card-red';
    if (score <= 60) return 'fut-card-orange';
    if (score <= 70) return 'fut-card-gold';
    return 'fut-card-gold-rare';
}

// Initialisation au chargement de la page
const params = new URLSearchParams(window.location.search);
const deputeId = params.get('id');

if (!deputeId) {
    document.getElementById('depute-content').innerHTML = `
        <p style="color: red; font-weight: bold;">Erreur : Aucun identifiant de député spécifié.</p>
    `;
} else {
    fetch('./data.json?t=' + Date.now())
        .then(res => {
            if (!res.ok) throw new Error("Impossible de charger data.json");
            return res.json();
        })
        .then(deputes => {
            const d = deputes.find(item => String(item.id).toLowerCase() === String(deputeId).toLowerCase());

            if (!d) {
                document.getElementById('depute-content').innerHTML = `
                    <p style="color: red; font-weight: bold;">Député introuvable dans la base de données.</p>
                `;
                return;
            }

            const scoreGlobal = d.score_global !== undefined
                ? d.score_global
                : (Object.values(d.scores || {}).length ? Math.round(Object.values(d.scores).reduce((a, b) => a + b, 0) / Object.values(d.scores).length) : 0);

            const bande = getBande(scoreGlobal);
            const futCardThemeClass = getFutCardThemeClass(scoreGlobal);

            const birthStr = d.date_naissance || d.dateNaissance || d.birthdate || d.birth_date;
            const computedAge = calculateAge(birthStr);
            const ageNum = computedAge !== null ? computedAge : (d.age ? d.age : '—');

            const photoPrincipal = d.photo_url || d.photo || d.photoUrl || d.avatar || `assets/deputes/${d.id}.jpg`;
            const photoFallbackPng = `assets/deputes/${d.id}.png`;
            const onlineAnPhoto = d.pa_id ? `https://www.assemblee-nationale.fr/dyn/static/tribun/17/photos/${d.pa_id}.jpg` : '';
            const svgDefault = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='35' r='25' fill='%23aaa'/><path d='M10 90 A40 40 0 0 1 90 90 Z' fill='%23aaa'/></svg>";

            const regionSlug = slugifyAsset(d.region);
            const regionUrl = d.blason_url || (regionSlug ? `assets/regions/${regionSlug}.png` : (d.drapeau_region || REGION_FLAGS[d.region]));

            const groupeName = d.parti || d.groupe || 'UDR';
            const partiSlug = slugifyAsset(groupeName);
            const partiUrl = d.logo_parti_url || (partiSlug ? `assets/partis/${partiSlug}.png` : (d.logo_parti || PARTY_LOGOS[groupeName]));

            const nomFamille = d.nom.split(' ').pop();
            const scores = d.scores || {};

            const pageTitle = `${d.nom} (${scoreGlobal}/100 - ${bande.label}) | Observatoire du Libéralisme`;
            const pageDesc = `Consultez le score libéral de ${d.nom} (${d.circo}) calculé selon les 6 piliers de la liberté économique.`;

            document.title = pageTitle;
            document.getElementById('og-title')?.setAttribute('content', pageTitle);
            document.getElementById('og-desc')?.setAttribute('content', pageDesc);
            document.getElementById('og-image')?.setAttribute('content', photoPrincipal);
            document.getElementById('og-url')?.setAttribute('content', window.location.href);

            document.getElementById('tw-title')?.setAttribute('content', pageTitle);
            document.getElementById('tw-desc')?.setAttribute('content', pageDesc);
            document.getElementById('tw-image')?.setAttribute('content', photoPrincipal);

            const drapeauRegionHtml = regionUrl
                ? `<img src="${regionUrl}" alt="Blason ${d.region || ''}" title="${d.region || ''}" referrerpolicy="no-referrer" onerror="this.style.display='none'">`
                : '';

            const partiHtml = partiUrl
                ? `<img src="${partiUrl}" alt="${groupeName}" title="${groupeName}" referrerpolicy="no-referrer" onerror="this.style.display='none'">`
                : '';

            const futCardHtml = `
                <div class="fut-card-large ${futCardThemeClass}">
                    <div class="fut-card-content">
                        <div class="fut-top">
                            <div class="fut-left-info">
                                <div class="fut-score-global">${scoreGlobal}</div>
                                <div class="fut-groupe">${d.groupe || 'UDR'}</div>
                            </div>
                            <div class="fut-age-badge" title="Âge du député">
                                ${ageNum} ANS
                            </div>
                        </div>

                        <div class="fut-photo-container">
                            <img src="${photoPrincipal}"
                                 alt="${d.nom}"
                                 onerror="if(!this.dataset.step){this.dataset.step=1; this.src='${photoFallbackPng}';}else if(this.dataset.step==='1'){this.dataset.step=2; this.src='${onlineAnPhoto}';}else{this.src='${svgDefault}';}">
                        </div>

                        <div class="fut-nom">${nomFamille}</div>

                        <div class="fut-stats-block">
                            <div class="fut-stats-grid">
                                <div class="fut-stat"><span class="fut-stat-val">${scores.FIS ?? 0}</span><span class="fut-stat-lbl">FISCALITÉ</span></div>
                                <div class="fut-stat"><span class="fut-stat-val">${scores.PRO ?? 0}</span><span class="fut-stat-lbl">PROPRIÉTÉ</span></div>
                                <div class="fut-stat"><span class="fut-stat-val">${scores.ETA ?? 0}</span><span class="fut-stat-lbl">ÉTAT</span></div>
                                <div class="fut-stat"><span class="fut-stat-val">${scores.LIB ?? 0}</span><span class="fut-stat-lbl">LIBERTÉ</span></div>
                                <div class="fut-stat"><span class="fut-stat-val">${scores.REG ?? 0}</span><span class="fut-stat-lbl">RÉGULATION</span></div>
                                <div class="fut-stat"><span class="fut-stat-val">${scores.OUV ?? 0}</span><span class="fut-stat-lbl">OUVERTURE</span></div>
                            </div>

                            <div class="fut-footer">
                                <div class="fut-footer-item">
                                    ${drapeauRegionHtml}
                                </div>
                                <div class="fut-footer-item" title="17e Législature">
                                    <span class="fut-badge-17">17ᵉ LÉG.</span>
                                </div>
                                <div class="fut-footer-item">
                                    ${partiHtml}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            let totalAbonnes = 0;
            let hasAbonnes = false;
            let socialBadgesHtml = '';

            if (d.email) {
                socialBadgesHtml += `
                    <a href="mailto:${d.email}" class="social-badge">
                        ✉️ Email : <strong>${d.email}</strong>
                    </a>
                `;
            }

            if (d.reseaux) {
                for (const [key, net] of Object.entries(d.reseaux)) {
                    let url = "";
                    let abonnees = 0;

                    if (typeof net === 'string') {
                        url = net;
                    } else if (net && typeof net === 'object') {
                        url = net.url || "";
                        abonnees = net.abonnees || 0;
                    }

                    if (url) {
                        const name = SOCIAL_NAMES[key.toLowerCase()] || key;
                        if (abonnees > 0) {
                            totalAbonnes += abonnees;
                            hasAbonnes = true;
                            socialBadgesHtml += `
                                <a href="${url}" target="_blank" rel="noopener" class="social-badge">
                                    🌐 ${name} : <strong>${formatNumber(abonnees)}</strong> abonnés ↗
                                </a>
                            `;
                        } else {
                            socialBadgesHtml += `
                                <a href="${url}" target="_blank" rel="noopener" class="social-badge">
                                    🌐 ${name} ↗
                                </a>
                            `;
                        }
                    }
                }
            }

            const socialTotalHtml = hasAbonnes ? `<div class="social-total">📢 Audience cumulée : ${formatNumber(totalAbonnes)} abonnés</div>` : '';

            const socialSectionHtml = socialBadgesHtml ? `
                <div class="social-box">
                    ${socialTotalHtml}
                    <div class="social-links">
                        ${socialBadgesHtml}
                    </div>
                </div>
            ` : '';

            const bioInlineHtml = d.biographie ? `
                <div class="bio-box-inline">
                    <h3 style="margin: 0 0 6px 0; font-size: 1rem; color: #1e293b;">📝 Biographie</h3>
                    <p style="color: #475569; line-height: 1.55; margin: 0; font-size: 0.92rem;">${d.biographie}</p>
                </div>
            ` : '';

            const syntheseHtml = d.synthese_analyse ? `
                <div class="social-box" style="margin-top: 15px; background-color: #fffbeb; border: 1px solid #fcd34d;">
                    <h3 style="margin: 0 0 8px 0; font-size: 1.1rem; color: #b45309;">💡 Analyse du profil économique (IA)</h3>
                    <p style="color: #78350f; line-height: 1.5; margin: 0; font-size: 0.95rem;">${d.synthese_analyse}</p>
                </div>
            ` : '';

            const datanBtnHtml = d.datanUrl
                ? `<a href="${d.datanUrl}" target="_blank" rel="noopener" class="datan-link">📊 Profil Datan.fr ↗</a>`
                : '';

            const statsHtml = (d.stats && (d.stats.participation || d.stats.loyaute_groupe)) ? `
                <div class="stats-grid">
                    ${d.stats.participation ? `
                        <div class="stat-card">
                            <span class="stat-value">${d.stats.participation}%</span>
                            <span class="stat-label">Participation aux votes</span>
                        </div>
                    ` : ''}
                    ${d.stats.loyaute_groupe ? `
                        <div class="stat-card">
                            <span class="stat-value">${d.stats.loyaute_groupe}%</span>
                            <span class="stat-label">Proximité avec son groupe</span>
                        </div>
                    ` : ''}
                </div>
            ` : '';

            const professionHtml = d.profession ? `
                <p style="margin-top: 6px; font-size: 0.95rem;">
                    💼 <strong>Profession :</strong> ${d.profession}
                </p>
            ` : '';

            // Génération de la décomposition des 6 piliers
            let pillarsHtml = '';
            for (const [code, info] of Object.entries(PILLARS_MAP)) {
                const score = (d.scores && d.scores[code] !== undefined) ? d.scores[code] : 0;
                const pBande = getBande(score);

                pillarsHtml += `
                    <div class="pillar-card">
                        <div class="pillar-title">
                            <span>${info.label}</span>
                            <span><strong>${score}</strong> / 100</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: ${score}%; background-color: ${pBande.color};"></div>
                        </div>
                        <small style="color: #64748b; margin-top: 6px; display: block;">${info.desc}</small>
                    </div>
                `;
            }

            // Génération de la liste des votes
            let votesHtml = '';
            const listVotes = d.votes || d.initiatives || [];

            if (listVotes.length > 0) {
                votesHtml = listVotes.map(vote => {
                    let badgeClass = 'badge-abstention';
                    if (vote.position === 'POUR') badgeClass = 'badge-pour';
                    if (vote.position === 'CONTRE') badgeClass = 'badge-contre';

                    return `
                        <div class="initiative-card">
                            <div class="initiative-header">
                                <span class="initiative-title">${vote.titre}</span>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span class="initiative-meta">📅 ${vote.date || 'Récents'}</span>
                                    ${vote.position ? `<span class="vote-badge ${badgeClass}">${vote.position}</span>` : ''}
                                </div>
                            </div>
                            ${vote.description ? `<p style="margin: 6px 0 0 0; color: #475569; font-size: 0.95rem;">${vote.description}</p>` : ''}
                            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-top: 8px;">
                                ${vote.pilier && PILLARS_MAP[vote.pilier] ? `<small style="color: #2563eb; font-weight: bold;">Pilier concerné : ${PILLARS_MAP[vote.pilier].label}</small>` : '<span></span>'}
                                ${vote.url ? `<a href="${vote.url}" target="_blank" rel="noopener" class="vote-link">Voir le vote sur Datan.fr ↗</a>` : ''}
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                votesHtml = '<p style="color: #64748b; font-style: italic;">Aucun vote répertorié pour le moment.</p>';
            }

            // Rendu final injecté dans le DOM
            document.getElementById('depute-content').innerHTML = `
                <div class="profile-header">
                    ${futCardHtml}
                    <div class="profile-info">
                        <h2>${d.nom}</h2>
                        <p><strong>Groupe :</strong> ${d.groupe || 'UDR'} | <strong>Circonscription :</strong> ${d.circo || 'N/C'}</p>
                        ${professionHtml}

                        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-top: 10px;">
                            <span class="badge ${bande.class}" style="font-size: 0.95rem; padding: 6px 12px;">
                                ${d.qualification || bande.label} — ${scoreGlobal} / 100
                            </span>
                            ${datanBtnHtml}
                        </div>

                        ${bioInlineHtml}
                        ${statsHtml}
                    </div>
                </div>

                ${syntheseHtml}
                ${socialSectionHtml}

                <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">

                <h3>📊 Décomposition selon les 6 piliers économiques</h3>
                <div class="pillar-grid">
                    ${pillarsHtml}
                </div>

                <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 25px 0;">

                <h3>📜 Votes enregistrés (${listVotes.length})</h3>
                <div style="margin-top: 10px;">
                    ${votesHtml}
                </div>
            `;
        })
        .catch(err => {
            console.error(err);
            document.getElementById('depute-content').innerHTML = `
                <p style="color: red; font-weight: bold;">Erreur : ${err.message}</p>
            `;
        });
}