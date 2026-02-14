/**
 * Simulations page JavaScript
 * Handles mode selection, participant management, question building,
 * image uploads, simulation execution, and results rendering.
 */

/* global individualsData, situationsData */

let selectedMode = null;
const participants = { conv: [], survey: [] };
const questions = [];

// ── Outcome tracking ──
document.getElementById('outcome-desc').addEventListener('input', updateOutcomeRunBtn);
document.getElementById('outcome-agent').addEventListener('change', updateOutcomeRunBtn);

function updateOutcomeRunBtn() {
    const desc = document.getElementById('outcome-desc').value.trim();
    const agent = document.getElementById('outcome-agent').value;
    document.getElementById('run-outcome').disabled = !desc || !agent;
}

function updateVaryBy(val) {
    document.querySelectorAll('.vary-option').forEach(o => o.classList.remove('active'));
    document.getElementById('vary-opt-' + val).classList.add('active');
    const sitGroup = document.getElementById('outcome-situation-group');
    const sitNote = document.getElementById('outcome-sit-note');
    if (val === 'situation') {
        sitGroup.style.opacity = '0.45';
        sitGroup.style.pointerEvents = 'none';
        sitNote.style.display = 'none';
    } else {
        sitGroup.style.opacity = '1';
        sitGroup.style.pointerEvents = 'auto';
        sitNote.style.display = 'inline';
    }
}

// ── Mode selection ──
function selectMode(mode) {
    selectedMode = mode;
    document.querySelectorAll('.mode-card').forEach(c => c.classList.remove('active'));
    document.getElementById('mode-' + mode).classList.add('active');
    document.querySelectorAll('.sim-config').forEach(c => c.classList.remove('visible'));
    document.getElementById('config-' + mode).classList.add('visible');
}

// ── Participants ──
function addParticipant(prefix) {
    const sel = document.getElementById(prefix + '-add-individual');
    const id = sel.value;
    if (!id) return;
    if (participants[prefix].find(p => p.id === id)) return;

    const name = sel.options[sel.selectedIndex].text;
    participants[prefix].push({ id, name });
    sel.value = '';
    renderParticipants(prefix);
    updateRunButton(prefix);
}

function removeParticipant(prefix, id) {
    participants[prefix] = participants[prefix].filter(p => p.id !== id);
    renderParticipants(prefix);
    updateRunButton(prefix);
}

function renderParticipants(prefix) {
    const area = document.getElementById(prefix + '-participants');
    const hint = document.getElementById(prefix + '-empty-hint');
    if (participants[prefix].length === 0) {
        area.innerHTML = '';
        area.appendChild(hint);
        hint.style.display = '';
        return;
    }
    hint.style.display = 'none';
    const chips = participants[prefix].map(p =>
        `<span class="participant-chip">
            🎭 ${p.name}
            <span class="remove-chip" onclick="removeParticipant('${prefix}','${p.id}')">✕</span>
        </span>`
    ).join('');
    area.innerHTML = chips;
}

function updateRunButton(prefix) {
    if (prefix === 'outcome') return;
    const btn = document.getElementById(prefix === 'conv' ? 'run-conversation' : 'run-survey');
    if (prefix === 'conv') {
        btn.disabled = participants.conv.length < 2;
    } else {
        btn.disabled = participants.survey.length < 1 || questions.length < 1;
    }
}

// ── Question builder ──
document.getElementById('q-type').addEventListener('change', function () {
    document.getElementById('mc-options-group').style.display =
        this.value === 'multiple_choice' ? '' : 'none';
});

function addQuestion() {
    const text = document.getElementById('q-text').value.trim();
    if (!text) return;
    const type = document.getElementById('q-type').value;
    const q = { id: 'q' + (questions.length + 1), text, type };
    if (type === 'multiple_choice') {
        const opts = document.getElementById('mc-options').value
            .split(',').map(s => s.trim()).filter(Boolean);
        if (opts.length < 2) { alert('Add at least 2 options'); return; }
        q.options = opts;
    }
    questions.push(q);
    document.getElementById('q-text').value = '';
    renderQuestions();
    updateRunButton('survey');
}

function removeQuestion(idx) {
    questions.splice(idx, 1);
    questions.forEach((q, i) => q.id = 'q' + (i + 1));
    renderQuestions();
    updateRunButton('survey');
}

function renderQuestions() {
    const list = document.getElementById('question-list');
    if (questions.length === 0) { list.innerHTML = ''; return; }
    list.innerHTML = questions.map((q, i) => `
        <div class="question-item">
            <span class="q-num">${i + 1}</span>
            <div class="q-body">
                <div class="q-text">${q.text}</div>
                <div class="q-type">${q.type.replace('_', ' ')}${q.options ? ' — ' + q.options.join(', ') : ''}</div>
            </div>
            <span class="q-remove" onclick="removeQuestion(${i})">✕</span>
        </div>
    `).join('');
}

// ── Image upload handling ──
window._surveyImageBase64 = null;
window._surveyImageMime = null;

function handleImageUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 4 * 1024 * 1024) {
        alert('Image must be under 4MB');
        return;
    }
    const reader = new FileReader();
    reader.onload = function (ev) {
        const dataUrl = ev.target.result;
        const [header, b64] = dataUrl.split(',');
        window._surveyImageBase64 = b64;
        window._surveyImageMime = file.type || 'image/png';

        document.getElementById('survey-image-thumb').src = dataUrl;
        document.getElementById('survey-image-name').textContent = file.name;
        document.getElementById('survey-image-placeholder').style.display = 'none';
        document.getElementById('survey-image-preview').style.display = '';
        document.getElementById('survey-image-area').style.borderColor = 'var(--primary)';
    };
    reader.readAsDataURL(file);
}

function clearImage() {
    window._surveyImageBase64 = null;
    window._surveyImageMime = null;
    document.getElementById('survey-image-input').value = '';
    document.getElementById('survey-image-placeholder').style.display = '';
    document.getElementById('survey-image-preview').style.display = 'none';
    document.getElementById('survey-image-area').style.borderColor = 'var(--border)';
}

// Drag-and-drop on the upload area
(function () {
    const area = document.getElementById('survey-image-area');
    if (!area) return;
    ['dragenter', 'dragover'].forEach(ev => {
        area.addEventListener(ev, e => { e.preventDefault(); area.style.borderColor = 'var(--primary)'; area.style.background = 'rgba(124,58,237,0.05)'; });
    });
    ['dragleave', 'drop'].forEach(ev => {
        area.addEventListener(ev, e => { e.preventDefault(); area.style.borderColor = 'var(--border)'; area.style.background = 'var(--primary-bg)'; });
    });
    area.addEventListener('drop', e => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            document.getElementById('survey-image-input').files = files;
            handleImageUpload({ target: { files } });
        }
    });
})();

// ── Run simulation ──
async function runSimulation(mode) {
    const btnId = mode === 'conversation' ? 'run-conversation'
        : mode === 'survey' ? 'run-survey' : 'run-outcome';
    const btn = document.getElementById(btnId);
    btn.classList.add('loading');
    btn.disabled = true;

    const payload = { mode };
    if (mode === 'conversation') {
        payload.individual_ids = participants.conv.map(p => p.id);
        payload.situation_id = document.getElementById('conv-situation').value || null;
        payload.max_turns = parseInt(document.getElementById('conv-turns').value);
        payload.variations = parseInt(document.getElementById('conv-variations').value);
    } else if (mode === 'survey') {
        payload.individual_ids = participants.survey.map(p => p.id);
        payload.situation_id = document.getElementById('survey-situation').value || null;
        payload.questions = questions;
        payload.variations = parseInt(document.getElementById('survey-variations').value);
        // Include image if uploaded
        if (window._surveyImageBase64) {
            payload.image_base64 = window._surveyImageBase64;
            payload.image_mime = window._surveyImageMime || 'image/png';
        }
        const imgDesc = document.getElementById('survey-image-desc');
        if (imgDesc && imgDesc.value.trim()) {
            payload.image_description = imgDesc.value.trim();
        }
    } else if (mode === 'outcome') {
        payload.outcome = document.getElementById('outcome-desc').value.trim();
        payload.scenario_context = document.getElementById('outcome-context').value.trim();
        payload.agent_id = document.getElementById('outcome-agent').value;
        payload.individual_ids = [payload.agent_id];
        payload.situation_id = document.getElementById('outcome-situation').value || null;
        payload.max_turns = parseInt(document.getElementById('outcome-turns').value);
        payload.num_trials = parseInt(document.getElementById('outcome-trials').value);
        payload.vary_by = document.querySelector('input[name="vary_by"]:checked').value;
    }

    try {
        const resp = await fetch('/simulations/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await resp.json();
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            renderResults(data);
        }
    } catch (err) {
        alert('Failed to run simulation: ' + err.message);
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
        if (mode === 'conversation') updateRunButton('conv');
        else if (mode === 'survey') updateRunButton('survey');
        else updateOutcomeRunBtn();
    }
}

// ── Render results ──
function renderResults(data) {
    if (data.mode === 'outcome') {
        renderOutcomeResults(data);
        return;
    }

    const area = document.getElementById('results-area');
    area.classList.add('visible');

    const variations = data.variations || [];
    const mode = data.mode;

    let tabsHtml = '';
    let panelsHtml = '';

    if (variations.length > 1) {
        tabsHtml = '<div class="variation-tabs">' +
            variations.map((v, i) => `<div class="variation-tab ${i === 0 ? 'active' : ''}" onclick="switchVariation(${i})">Variation ${i + 1}</div>`).join('') +
            '</div>';
    }

    variations.forEach((variation, vi) => {
        const activeClass = vi === 0 ? 'active' : '';
        if (mode === 'conversation') {
            const turns = variation.turns || [];
            const speakerNames = [...new Set(turns.map(t => t.speaker))];
            const turnsHtml = turns.map((t, ti) => {
                const idx = speakerNames.indexOf(t.speaker) % 4;
                const radarId = `radar-${vi}-${ti}`;
                let radarHtml = '';
                if (t.radar && t.radar.values && t.radar.values.some(v => v > 0)) {
                    const emotionChips = t.radar.emotions ? Object.entries(t.radar.emotions)
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 6)
                        .map(([name, val]) => `<span class="emo-chip">${name} <span class="emo-val">${Math.round(val * 100)}%</span></span>`)
                        .join('') : '';
                    radarHtml = `<div class="turn-radar-wrap" id="wrap-${radarId}">
                        <div class="turn-radar-canvas"><canvas id="${radarId}" width="160" height="160"></canvas></div>
                        <div class="turn-radar-emotions">${emotionChips}</div>
                    </div>`;
                }
                return `<div class="conv-turn speaker-${idx}">
                    <div class="speaker-name">${t.speaker}</div>
                    <div class="turn-content">${t.content}</div>
                    ${radarHtml}
                </div>`;
            }).join('');
            panelsHtml += `<div class="variation-panel ${activeClass}" data-variation="${vi}">
                <div class="conversation-display">${turnsHtml}</div>
            </div>`;
        } else {
            // Survey
            const respondents = variation.respondents || [];
            let surveyHtml = '';
            respondents.forEach(r => {
                const answersHtml = (r.answers || []).map((a, qi) => {
                    let ratingBadge = '';
                    if (a.rating !== undefined && a.rating !== null) {
                        ratingBadge = `<span class="sa-rating">${a.rating}</span>`;
                    }
                    return `<div class="survey-answer">
                        <div class="sa-question">
                            <span class="sa-num">${qi + 1}</span>
                            ${a.question}
                        </div>
                        <div class="sa-response">${ratingBadge}${a.response}</div>
                    </div>`;
                }).join('');
                surveyHtml += `<div class="survey-respondent">
                    <h3>🎭 ${r.name}</h3>
                    ${answersHtml}
                </div>`;
            });
            panelsHtml += `<div class="variation-panel ${activeClass}" data-variation="${vi}">
                <div class="survey-results">${surveyHtml}</div>
            </div>`;
        }
    });

    const icon = mode === 'conversation' ? '💬' : '📋';
    const title = mode === 'conversation' ? 'Conversation Results' : 'Survey Results';
    const meta = mode === 'conversation'
        ? `${data.turn_count || 0} turns · ${variations.length} variation(s)`
        : `${data.question_count || 0} questions · ${data.respondent_count || 0} respondent(s)`;

    area.innerHTML = `
        <div class="results-header">
            <h2>${icon} ${title}</h2>
            <span class="result-meta">${meta}</span>
        </div>
        ${tabsHtml}
        ${panelsHtml}
    `;
    area.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── Render outcome results ──
function renderOutcomeResults(data) {
    const area = document.getElementById('results-area');
    area.classList.add('visible');

    const trials = data.trials || [];
    const varyBy = data.vary_by || 'traits';
    const successCount = trials.filter(t => t.outcome && t.outcome.achieved).length;
    const totalCount = trials.length;
    const successRate = totalCount > 0 ? Math.round((successCount / totalCount) * 100) : 0;

    // Gauge color
    let gaugeColor = '#ef4444';
    if (successRate >= 60) gaugeColor = '#34d399';
    else if (successRate >= 40) gaugeColor = '#facc15';
    else if (successRate >= 20) gaugeColor = '#f97316';

    // --- Build correlation section based on vary_by ---
    let corrSectionHtml = '';
    let tipHtml = '';
    const varyLabels = { traits: '🧬 Personality Traits', emotions: '💭 Emotional State', situation: '📍 Situation' };
    const corrTitle = (varyLabels[varyBy] || 'Traits') + ' — Correlations with Success';

    if (varyBy === 'situation') {
        const sitCorr = data.situation_correlations || {};
        let sitBarsHtml = '';
        for (const [param, values] of Object.entries(sitCorr)) {
            const paramLabel = param.replace(/_/g, ' ');
            sitBarsHtml += `<div style="margin-bottom:1rem;"><h4 style="color:var(--primary);font-size:0.9rem;margin-bottom:0.5rem;text-transform:capitalize;">${paramLabel}</h4>`;
            for (const [val, info] of Object.entries(values)) {
                const rate = Math.round(info.success_rate * 100);
                const barColor = rate >= 50 ? '#34d399' : rate >= 25 ? '#facc15' : '#f87171';
                sitBarsHtml += `<div class="trait-bar-item">
                    <span class="trait-bar-name">${val.replace(/_/g, ' ')}</span>
                    <div class="trait-bar-wrap">
                        <div class="trait-bar-fill positive" style="left:0;width:${rate}%;background:${barColor};"></div>
                    </div>
                    <span class="trait-bar-value" style="color:${barColor};">${rate}% (${info.success_count}/${info.total_count})</span>
                </div>`;
            }
            sitBarsHtml += '</div>';
        }
        corrSectionHtml = sitBarsHtml || '<p style="color:var(--text-muted);font-size:0.85rem;">Need more trials for correlation data</p>';

        const modCorr = sitCorr.modality || {};
        const bestMod = Object.entries(modCorr).sort((a, b) => b[1].success_rate - a[1].success_rate)[0];
        const worstMod = Object.entries(modCorr).sort((a, b) => a[1].success_rate - b[1].success_rate)[0];
        if (bestMod && worstMod && bestMod[0] !== worstMod[0]) {
            tipHtml = `<div class="outcome-tip"><h4>💡 Key Insight</h4>
                <p><b>${bestMod[0].replace(/_/g, ' ')}</b> had the highest success rate (${Math.round(bestMod[1].success_rate * 100)}%).`;
            if (worstMod[1].success_rate < bestMod[1].success_rate) {
                tipHtml += ` <b>${worstMod[0].replace(/_/g, ' ')}</b> had the lowest (${Math.round(worstMod[1].success_rate * 100)}%).`;
            }
            tipHtml += '</p></div>';
        }
    } else {
        const correlations = varyBy === 'emotions' ? (data.emotion_correlations || {}) : (data.trait_correlations || {});
        const corrEntries = Object.entries(correlations).slice(0, 10);
        const maxDiff = Math.max(0.01, ...corrEntries.map(([, v]) => Math.abs(v.difference)));
        corrSectionHtml = corrEntries.map(([name, info]) => {
            const diff = info.difference;
            const pct = Math.abs(diff) / maxDiff * 48;
            const isPos = diff > 0;
            const barClass = isPos ? 'positive' : 'negative';
            const barStyle = isPos
                ? `left: 50%; width: ${pct}%;`
                : `right: 50%; width: ${pct}%;`;
            const sign = isPos ? '+' : '';
            const displayName = name.replace(/_/g, ' ');
            return `<div class="trait-bar-item">
                <span class="trait-bar-name">${displayName}</span>
                <div class="trait-bar-wrap">
                    <div class="trait-bar-center"></div>
                    <div class="trait-bar-fill ${barClass}" style="${barStyle}"></div>
                </div>
                <span class="trait-bar-value ${barClass}">${sign}${(diff * 100).toFixed(0)}%</span>
            </div>`;
        }).join('');
        if (!corrSectionHtml) corrSectionHtml = '<p style="color:var(--text-muted);font-size:0.85rem;">Need more trials for correlation data</p>';

        // Insight tip
        const corrEntries2 = Object.entries(varyBy === 'emotions' ? (data.emotion_correlations || {}) : (data.trait_correlations || {})).slice(0, 10);
        if (corrEntries2.length > 0) {
            const topPos = corrEntries2.filter(([, v]) => v.difference > 0.05).slice(0, 2);
            const topNeg = corrEntries2.filter(([, v]) => v.difference < -0.05).slice(0, 2);
            let tipParts = [];
            if (topPos.length) tipParts.push(`Higher <b>${topPos.map(([t]) => t.replace(/_/g, ' ')).join('</b> and <b>')}</b> correlated with success.`);
            if (topNeg.length) tipParts.push(`Higher <b>${topNeg.map(([t]) => t.replace(/_/g, ' ')).join('</b> and <b>')}</b> tended to reduce success.`);
            if (tipParts.length) {
                tipHtml = `<div class="outcome-tip"><h4>💡 Key Insight</h4><p>${tipParts.join(' ')}</p></div>`;
            }
        }
    }

    // Per-trial items
    const trialsHtml = trials.map((trial, ti) => {
        const achieved = trial.outcome && trial.outcome.achieved;
        const badge = achieved
            ? '<span class="trial-badge success">✓ Achieved</span>'
            : '<span class="trial-badge failure">✗ Not Achieved</span>';

        let chips = '';
        if (varyBy === 'traits') {
            const traits = trial.customer_traits || {};
            chips = Object.entries(traits)
                .sort((a, b) => b[1] - a[1]).slice(0, 4)
                .map(([k, v]) => `<span class="tt">${k.replace(/_/g, ' ')} ${Math.round(v * 100)}%</span>`)
                .join('');
        } else if (varyBy === 'emotions') {
            const emos = trial.customer_emotions || {};
            chips = Object.entries(emos)
                .sort((a, b) => b[1] - a[1]).slice(0, 4)
                .map(([k, v]) => `<span class="tt">${k.replace(/_/g, ' ')} ${Math.round(v * 100)}%</span>`)
                .join('');
        } else {
            const sp = trial.situation_params || {};
            chips = `<span class="tt">${(sp.modality || '').replace(/_/g, ' ')}</span><span class="tt">${sp.location || ''}</span>`;
        }

        const reasoning = trial.outcome ? trial.outcome.reasoning : '';
        const turns = trial.conversation || [];
        const speakerNames = [...new Set(turns.map(t => t.speaker))];
        const convHtml = turns.map(t => {
            const idx = speakerNames.indexOf(t.speaker) % 4;
            return `<div class="conv-turn speaker-${idx}">
                <div class="speaker-name">${t.speaker}</div>
                <div class="turn-content">${t.content}</div>
            </div>`;
        }).join('');

        return `<div class="trial-item">
            <div class="trial-header" onclick="this.nextElementSibling.classList.toggle('open'); this.querySelector('.trial-expand').textContent = this.nextElementSibling.classList.contains('open') ? '▼' : '▶'">
                ${badge}
                <span class="trial-name">Trial ${ti + 1}: ${trial.customer_name || 'Unknown'}</span>
                <span class="trial-traits">${chips}</span>
                <span class="trial-expand">▶</span>
            </div>
            <div class="trial-body">
                <div class="trial-reasoning">💡 ${reasoning}</div>
                <div class="trial-conv">${convHtml}</div>
            </div>
        </div>`;
    }).join('');

    const varyBadge = { traits: '🧬 Varying Personality Traits', emotions: '💭 Varying Emotional State', situation: '📍 Varying Situation' };
    const scenarioCtx = data.scenario_context || '';
    const ctxLine = scenarioCtx
        ? `<div style="font-size:0.8rem;color:var(--text-muted);margin-top:0.25rem;font-style:italic;max-width:700px;">📋 ${scenarioCtx}</div>`
        : '';

    area.innerHTML = `
        <div class="results-header">
            <h2>🎯 Outcome Tracking Results</h2>
            <span class="result-meta">${totalCount} trials · ${data.turns_per_trial || 0} turns/trial · ${varyBadge[varyBy] || ''}</span>
            ${ctxLine}
        </div>
        <div class="outcome-dashboard">
            <div class="outcome-summary">
                <div class="outcome-gauge">
                    <div class="gauge-circle" style="--gauge-pct: ${successRate}; --gauge-color: ${gaugeColor}">
                        <span class="gauge-value">${successRate}%</span>
                    </div>
                    <div class="gauge-label">${successCount}/${totalCount} achieved</div>
                    <div class="gauge-sublabel">"${data.outcome_description || ''}"</div>
                </div>
                <div class="trait-correlations">
                    <h3>📊 ${corrTitle}</h3>
                    ${corrSectionHtml}
                </div>
            </div>
            ${tipHtml}
            <div class="outcome-trials">
                <h3>📋 Individual Trials (click to expand)</h3>
                ${trialsHtml}
            </div>
        </div>
    `;
    area.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function switchVariation(idx) {
    document.querySelectorAll('.variation-tab').forEach((t, i) => t.classList.toggle('active', i === idx));
    document.querySelectorAll('.variation-panel').forEach((p, i) => p.classList.toggle('active', i === idx));
}

// ── Mini Radar drawing ──
const CAT_COLORS = {
    Joy: '#facc15', Powerful: '#f97316', Peaceful: '#34d399',
    Anger: '#ef4444', Sad: '#60a5fa', Fear: '#a78bfa',
};

function drawMiniRadar(canvasId, radarData) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !radarData) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const cx = W / 2, cy = H / 2;
    const R = Math.min(cx, cy) - 28;
    const cats = radarData.categories;
    const vals = radarData.values;
    const n = cats.length;
    if (!n) return;

    ctx.clearRect(0, 0, W, H);

    // Grid rings
    for (let ring = 1; ring <= 4; ring++) {
        const r = R * (ring / 4);
        ctx.beginPath();
        for (let i = 0; i <= n; i++) {
            const angle = (Math.PI * 2 * (i % n)) / n - Math.PI / 2;
            const x = cx + r * Math.cos(angle);
            const y = cy + r * Math.sin(angle);
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.strokeStyle = 'rgba(108,92,231,' + (ring === 4 ? 0.18 : 0.07) + ')';
        ctx.lineWidth = 0.5;
        ctx.stroke();
    }

    // Axes
    for (let i = 0; i < n; i++) {
        const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + R * Math.cos(angle), cy + R * Math.sin(angle));
        ctx.strokeStyle = 'rgba(108,92,231,0.1)';
        ctx.lineWidth = 0.5;
        ctx.stroke();
    }

    // Axis labels
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    for (let i = 0; i < n; i++) {
        const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
        const labelR = R + 16;
        const x = cx + labelR * Math.cos(angle);
        const y = cy + labelR * Math.sin(angle);
        const pct = Math.round(vals[i] * 100);
        ctx.font = "600 8px 'Quicksand', 'Inter', sans-serif";
        ctx.fillStyle = CAT_COLORS[cats[i]] || '#636e72';
        ctx.fillText(cats[i], x, y);
        if (pct > 0) {
            ctx.font = "700 7px 'Quicksand', 'Inter', sans-serif";
            ctx.fillStyle = 'rgba(100,100,120,0.6)';
            ctx.fillText(pct + '%', x, y + 10);
        }
    }

    // Data polygon
    ctx.beginPath();
    for (let i = 0; i <= n; i++) {
        const angle = (Math.PI * 2 * (i % n)) / n - Math.PI / 2;
        const v = vals[i % n];
        const x = cx + R * v * Math.cos(angle);
        const y = cy + R * v * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = 'rgba(108, 92, 231, 0.12)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(108, 92, 231, 0.55)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Data points
    for (let i = 0; i < n; i++) {
        const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
        const v = vals[i];
        const x = cx + R * v * Math.cos(angle);
        const y = cy + R * v * Math.sin(angle);
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fillStyle = CAT_COLORS[cats[i]] || '#6c5ce7';
        ctx.fill();
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 1.5;
        ctx.stroke();
    }
}

// Store last results for radar drawing
let _lastResultData = null;

const _origRenderResults = renderResults;
renderResults = function (data) {
    _lastResultData = data;
    _origRenderResults(data);
    // Draw all mini radars after DOM is updated
    requestAnimationFrame(() => {
        if (data.mode === 'conversation') {
            (data.variations || []).forEach((variation, vi) => {
                (variation.turns || []).forEach((t, ti) => {
                    if (t.radar && t.radar.values && t.radar.values.some(v => v > 0)) {
                        drawMiniRadar(`radar-${vi}-${ti}`, t.radar);
                    }
                });
            });
        }
    });
};

// ── History panel ──

function toggleHistory() {
    const panel = document.getElementById('history-panel');
    if (panel) {
        panel.classList.toggle('collapsed');
    }
}

async function replaySimulation(simId) {
    const item = document.getElementById('hist-' + simId);
    if (item) item.classList.add('loading');

    try {
        const resp = await fetch('/simulations/history/' + simId);
        const envelope = await resp.json();
        if (envelope.error) {
            alert('Error: ' + envelope.error);
            return;
        }
        // The actual result data is inside the envelope
        const data = envelope.result || envelope;
        renderResults(data);
    } catch (err) {
        alert('Failed to load simulation: ' + err.message);
    } finally {
        if (item) item.classList.remove('loading');
    }
}

async function deleteSimulation(simId) {
    if (!confirm('Delete this simulation?')) return;

    try {
        const resp = await fetch('/simulations/history/' + simId, { method: 'DELETE' });
        if (resp.ok) {
            const item = document.getElementById('hist-' + simId);
            if (item) {
                item.style.transition = 'all 0.3s ease';
                item.style.opacity = '0';
                item.style.maxHeight = '0';
                item.style.padding = '0';
                item.style.margin = '0';
                setTimeout(() => {
                    item.remove();
                    // Update count badge
                    const panel = document.getElementById('history-panel');
                    const remaining = panel ? panel.querySelectorAll('.history-item').length : 0;
                    const badge = panel ? panel.querySelector('.history-count') : null;
                    if (badge) badge.textContent = remaining;
                    if (remaining === 0 && panel) panel.remove();
                }, 300);
            }
        } else {
            alert('Failed to delete simulation');
        }
    } catch (err) {
        alert('Failed to delete: ' + err.message);
    }
}
