/**
 * Personaut Chat Interface — Client JavaScript
 * Handles message sending, radar chart, memories, masks, triggers.
 */

/* ── Chat Messaging ── */
let sending = false;

function sendMessage(sessionId) {
    const input = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    if (!input.value.trim() || sending) return;
    sending = true;
    sendBtn.disabled = true;

    const text = input.value;
    const messages = document.getElementById('messages');

    // Show sent message
    const msg = document.createElement('div');
    msg.className = 'message sent';
    msg.textContent = text;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
    input.value = '';

    // Show typing indicator
    const typing = document.createElement('div');
    typing.className = 'message received';
    typing.id = 'typing-indicator';
    typing.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;

    // POST to Flask proxy
    fetch('/chat/' + sessionId + '/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text }),
    })
        .then((r) => r.json())
        .then((data) => {
            const ti = document.getElementById('typing-indicator');
            if (ti) ti.remove();

            if (data.reply) {
                const reply = document.createElement('div');
                reply.className = 'message received';
                const sender = document.createElement('div');
                sender.className = 'message-sender';
                sender.textContent = data.reply_sender || 'Character';
                reply.appendChild(sender);
                reply.appendChild(document.createTextNode(data.reply));

                // Token usage badge
                if (
                    data.usage &&
                    (data.usage.prompt_tokens || data.usage.completion_tokens)
                ) {
                    const badge = document.createElement('div');
                    badge.className = 'token-badge';
                    const pt = data.usage.prompt_tokens || 0;
                    const ct = data.usage.completion_tokens || 0;
                    badge.innerHTML =
                        '<span class="token-item prompt" title="Prompt tokens">↑' +
                        pt.toLocaleString() +
                        '</span>' +
                        '<span class="token-item completion" title="Completion tokens">↓' +
                        ct.toLocaleString() +
                        '</span>' +
                        '<span class="token-item">' +
                        (pt + ct).toLocaleString() +
                        ' total</span>';
                    reply.appendChild(badge);
                }

                // Activation info badges
                if (data.activation) {
                    const act = data.activation;
                    const hasInfo =
                        (act.activated_masks && act.activated_masks.length) ||
                        (act.fired_triggers && act.fired_triggers.length) ||
                        (act.relevant_memories && act.relevant_memories.length);
                    if (hasInfo) {
                        const actDiv = document.createElement('div');
                        actDiv.className = 'activation-info';
                        let html = '';
                        if (act.activated_masks && act.activated_masks.length) {
                            act.activated_masks.forEach((m) => {
                                html +=
                                    '<span class="act-badge act-mask" title="' +
                                    (m.description || '') +
                                    '">🎭 ' +
                                    m.name +
                                    '</span>';
                            });
                        }
                        if (act.fired_triggers && act.fired_triggers.length) {
                            act.fired_triggers.forEach((t) => {
                                html +=
                                    '<span class="act-badge act-trigger" title="Type: ' +
                                    t.type +
                                    '">⚡ ' +
                                    t.description +
                                    '</span>';
                            });
                        }
                        if (act.relevant_memories && act.relevant_memories.length) {
                            html +=
                                '<span class="act-badge act-memory" title="Memories consulted">🧠 ' +
                                act.relevant_memories.length +
                                ' memories</span>';
                        }
                        actDiv.innerHTML = html;
                        reply.appendChild(actDiv);
                    }
                }

                messages.appendChild(reply);
                messages.scrollTop = messages.scrollHeight;

                // Update session total in header
                if (data.session_totals) {
                    const totalEl = document.getElementById('token-total-val');
                    if (totalEl)
                        totalEl.textContent = (
                            data.session_totals.total_tokens || 0
                        ).toLocaleString();
                    const promptEls = document.querySelectorAll(
                        '#token-total .prompt'
                    );
                    if (promptEls.length)
                        promptEls[0].textContent =
                            '\u2191' +
                            (
                                data.session_totals.prompt_tokens || 0
                            ).toLocaleString();
                    const compEls = document.querySelectorAll(
                        '#token-total .completion'
                    );
                    if (compEls.length)
                        compEls[0].textContent =
                            '\u2193' +
                            (
                                data.session_totals.completion_tokens || 0
                            ).toLocaleString();
                }

                // Update emotional state radar
                if (data.radar && typeof drawRadar === 'function') {
                    const panel = document.getElementById('radar-panel');
                    if (panel) {
                        panel.style.transition = 'box-shadow 0.6s ease';
                        panel.style.boxShadow =
                            '0 0 24px rgba(108,92,231,0.25)';
                        setTimeout(() => {
                            panel.style.boxShadow = '';
                        }, 800);
                    }
                    drawRadar(data.radar);
                }
            }
        })
        .catch(() => {
            const ti = document.getElementById('typing-indicator');
            if (ti) ti.remove();
            const err = document.createElement('div');
            err.className = 'message received';
            err.innerHTML = '<em class="error-message">Failed to send message</em>';
            messages.appendChild(err);
        })
        .finally(() => {
            sending = false;
            sendBtn.disabled = false;
            input.focus();
        });
}

/* ── Radar Chart ── */
function drawRadar(radarOverride) {
    const data =
        radarOverride ||
        (typeof RADAR_DATA !== 'undefined' && RADAR_DATA.length
            ? RADAR_DATA[0]
            : null);
    if (!data) return;
    const canvas = document.getElementById('radar-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width,
        H = canvas.height;
    const cx = W / 2,
        cy = H / 2;
    const R = Math.min(cx, cy) - 30;
    const cats = data.categories;
    const vals = data.values;
    const n = cats.length;

    ctx.clearRect(0, 0, W, H);

    // Grid rings
    for (let ring = 1; ring <= 4; ring++) {
        const r = R * (ring / 4);
        ctx.beginPath();
        for (let i = 0; i <= n; i++) {
            const angle = (Math.PI * 2 * (i % n)) / n - Math.PI / 2;
            const x = cx + r * Math.cos(angle);
            const y = cy + r * Math.sin(angle);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.strokeStyle =
            'rgba(108,92,231,' + (ring === 4 ? 0.2 : 0.08) + ')';
        ctx.lineWidth = 1;
        ctx.stroke();
    }

    // Axes
    for (let i = 0; i < n; i++) {
        const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + R * Math.cos(angle), cy + R * Math.sin(angle));
        ctx.strokeStyle = 'rgba(108,92,231,0.1)';
        ctx.lineWidth = 1;
        ctx.stroke();
    }

    // Axis labels
    ctx.font = "600 10px 'Quicksand', sans-serif";
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    for (let i = 0; i < n; i++) {
        const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
        const labelR = R + 18;
        const x = cx + labelR * Math.cos(angle);
        const y = cy + labelR * Math.sin(angle);
        ctx.fillStyle = CAT_COLORS[cats[i]] || '#636e72';
        ctx.fillText(cats[i], x, y);
    }

    // Data polygon (filled)
    ctx.beginPath();
    for (let i = 0; i <= n; i++) {
        const angle = (Math.PI * 2 * (i % n)) / n - Math.PI / 2;
        const v = vals[i % n];
        const x = cx + R * v * Math.cos(angle);
        const y = cy + R * v * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = 'rgba(108, 92, 231, 0.12)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(108, 92, 231, 0.5)';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Data points
    for (let i = 0; i < n; i++) {
        const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
        const v = vals[i];
        const x = cx + R * v * Math.cos(angle);
        const y = cy + R * v * Math.sin(angle);
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = CAT_COLORS[cats[i]] || '#6c5ce7';
        ctx.fill();
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 1.5;
        ctx.stroke();
    }

    // Build legend
    const legend = document.getElementById('radar-legend');
    if (!legend) return;
    let html = '';
    for (let i = 0; i < n; i++) {
        const color = CAT_COLORS[cats[i]] || '#636e72';
        const pct = Math.round(vals[i] * 100);
        html +=
            '<div class="radar-legend-item">' +
            '<div class="radar-legend-dot" style="background:' +
            color +
            '"></div>' +
            '<span class="radar-legend-label">' +
            cats[i] +
            '</span>' +
            '<span class="radar-legend-value">' +
            pct +
            '%</span>' +
            '</div>';
    }

    // Active emotions as chips
    const emotions = data.emotions;
    if (emotions && Object.keys(emotions).length > 0) {
        html +=
            '<div class="emotions-section-label">' +
            '<div class="section-label">Active Emotions</div>' +
            '<div class="radar-emotions">';
        for (const [name, val] of Object.entries(emotions).sort(
            (a, b) => b[1] - a[1]
        )) {
            html +=
                '<span class="radar-emotion-chip">' +
                name +
                ' <span class="intensity">' +
                Math.round(val * 100) +
                '%</span></span>';
        }
        html += '</div></div>';
    }
    legend.innerHTML = html;
}

/* ── Panel Toggles ── */
function toggleRadar() {
    togglePanel('radar-body', 'radar-toggle');
}

function toggleMemories() {
    togglePanel('memories-body', 'memories-toggle');
}

function toggleMasks() {
    togglePanel('masks-body', 'masks-toggle');
}

function toggleTriggers() {
    togglePanel('triggers-body', 'triggers-toggle');
}

function togglePanel(bodyId, toggleId) {
    const body = document.getElementById(bodyId);
    const toggle = document.getElementById(toggleId);
    if (!body) return;
    if (body.classList.contains('collapsed')) {
        body.classList.remove('collapsed');
        if (toggle) toggle.textContent = '▼';
    } else {
        body.classList.add('collapsed');
        if (toggle) toggle.textContent = '▶';
    }
}

/* ── Utility Parsers ── */
function parseEmotions(str) {
    if (!str || !str.trim()) return null;
    const result = {};
    for (const part of str.split(',')) {
        const [k, v] = part.split('=').map((s) => s.trim());
        if (k && v) result[k] = parseFloat(v) || 0;
    }
    return Object.keys(result).length > 0 ? result : null;
}

function parseMods(str) {
    if (!str || !str.trim()) return {};
    const result = {};
    for (const part of str.split(',')) {
        const [k, v] = part.split('=').map((s) => s.trim());
        if (k && v) result[k] = parseFloat(v) || 0;
    }
    return result;
}

function parseRules(str) {
    if (!str || !str.trim()) return [];
    const rules = [];
    for (const part of str.split(',')) {
        const trimmed = part.trim();
        const match = trimmed.match(/^(\w+)\s*([><!=]+)\s*([\d.]+)$/);
        if (match) {
            rules.push({
                field: match[1],
                operator: match[2],
                threshold: parseFloat(match[3]),
            });
        }
    }
    return rules;
}

/* ── Memory Management ── */
function initSalienceSlider() {
    const slider = document.getElementById('new-memory-salience');
    const display = document.getElementById('salience-display');
    if (slider && display) {
        slider.addEventListener('input', function () {
            display.textContent = this.value + '%';
        });
    }
}

function addMemory() {
    const desc = document.getElementById('new-memory-desc');
    const sal = document.getElementById('new-memory-salience');
    const emo = document.getElementById('new-memory-emotions');
    if (!desc || !desc.value.trim()) return;

    const payload = {
        description: desc.value.trim(),
        salience: parseInt(sal.value) / 100,
        emotional_state: parseEmotions(emo.value),
    };

    fetch('/chat/' + SESSION_ID + '/memories/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    })
        .then((r) => r.json())
        .then((data) => {
            if (data.error) {
                alert(data.error);
                return;
            }
            const list = document.getElementById('memory-list');
            const noMsg = document.getElementById('no-memories-msg');
            if (noMsg) noMsg.remove();

            const salPct = Math.round(data.salience * 100);
            const emoStr = data.emotional_state
                ? ' · <span class="emo-tags">' +
                Object.keys(data.emotional_state).join(', ') +
                '</span>'
                : '';
            const salClass =
                salPct >= 80
                    ? 'salience-high'
                    : salPct >= 50
                        ? 'salience-mid'
                        : 'salience-low';

            const div = document.createElement('div');
            div.className = 'memory-item';
            div.id = 'mem-' + data.id;
            div.innerHTML =
                '<div class="item-content">' +
                '<div class="item-text">' +
                data.description +
                '</div>' +
                '<div class="item-meta">' +
                'salience: <span class="' +
                salClass +
                '">' +
                salPct +
                '%</span>' +
                emoStr +
                '</div></div>' +
                '<button onclick="deleteMemory(' +
                JSON.stringify(data.id) +
                ')" class="btn-delete" title="Delete memory">✕</button>';
            list.appendChild(div);

            const badge = document.getElementById('memory-count-badge');
            if (badge)
                badge.textContent =
                    '(' + list.querySelectorAll('.memory-item').length + ')';

            desc.value = '';
            sal.value = 50;
            document.getElementById('salience-display').textContent = '50%';
            emo.value = '';
        });
}

function deleteMemory(memoryId) {
    fetch('/chat/' + SESSION_ID + '/memories/' + memoryId + '/delete', {
        method: 'POST',
    })
        .then((r) => r.json())
        .then((data) => {
            if (data.ok) {
                const el = document.getElementById('mem-' + memoryId);
                if (el) el.remove();
                const badge = document.getElementById('memory-count-badge');
                const list = document.getElementById('memory-list');
                if (badge && list)
                    badge.textContent =
                        '(' +
                        list.querySelectorAll('.memory-item').length +
                        ')';
            }
        });
}

function searchMemories() {
    const input = document.getElementById('memory-search-input');
    if (!input || !input.value.trim()) {
        document
            .querySelectorAll('.memory-item')
            .forEach((el) => (el.style.display = ''));
        return;
    }

    fetch('/chat/' + SESSION_ID + '/memories/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input.value.trim() }),
    })
        .then((r) => r.json())
        .then((data) => {
            const matchedIds = new Set(
                (data.results || []).map((m) => 'mem-' + m.id)
            );
            document.querySelectorAll('.memory-item').forEach((el) => {
                el.style.display = matchedIds.has(el.id) ? '' : 'none';
            });
        });
}

/* ── Mask Management ── */
const MASK_PRESETS = {
    professional: {
        name: 'Professional',
        description:
            'Workplace persona that suppresses strong emotions and promotes calm, composed behavior.',
        emotional_modifications: {
            angry: -0.5, hostile: -0.5, hateful: -0.6, critical: -0.3,
            excited: -0.3, content: 0.2, satisfied: 0.2, thoughtful: 0.3,
        },
        trigger_situations: [
            'office', 'meeting', 'professional', 'work', 'conference',
            'presentation', 'interview', 'client',
        ],
    },
    casual: {
        name: 'Casual',
        description:
            'Relaxed persona for informal social situations that allows more natural emotional expression.',
        emotional_modifications: {
            excited: 0.2, cheerful: 0.2, energetic: 0.2, insecure: -0.2,
            anxious: -0.2, loving: 0.1, trusting: 0.2,
        },
        trigger_situations: [
            'party', 'friends', 'casual', 'hanging out', 'relaxing',
            'weekend', 'bar', 'home',
        ],
    },
    stoic: {
        name: 'Stoic',
        description: 'Calm, unflappable persona for crisis situations.',
        emotional_modifications: {
            angry: -0.6, anxious: -0.5, helpless: -0.4, confused: -0.3,
            insecure: -0.4, excited: -0.4, depressed: -0.3, content: 0.3,
            thoughtful: 0.4, satisfied: 0.2,
        },
        trigger_situations: [
            'crisis', 'emergency', 'danger', 'high stakes', 'stressful',
            'pressure', 'urgent',
        ],
    },
    enthusiastic: {
        name: 'Enthusiastic',
        description: 'High-energy persona for motivational contexts.',
        emotional_modifications: {
            excited: 0.4, cheerful: 0.4, hopeful: 0.3, energetic: 0.5,
            creative: 0.3, bored: -0.4, apathetic: -0.5, depressed: -0.3,
            proud: 0.2,
        },
        trigger_situations: [
            'rally', 'motivational', 'celebration', 'achievement', 'success',
            'launch', 'inspiring',
        ],
    },
    nurturing: {
        name: 'Nurturing',
        description:
            'Caring, supportive persona promoting warmth and patience.',
        emotional_modifications: {
            loving: 0.4, nurturing: 0.5, intimate: 0.3, trusting: 0.3,
            angry: -0.4, critical: -0.4, hostile: -0.5, selfish: -0.5,
            content: 0.2,
        },
        trigger_situations: [
            'child', 'caring', 'nursing', 'teaching', 'mentoring',
            'comforting', 'supporting',
        ],
    },
    guarded: {
        name: 'Guarded',
        description:
            'Protective persona for unfamiliar or potentially hostile situations.',
        emotional_modifications: {
            trusting: -0.4, intimate: -0.5, loving: -0.3, anxious: 0.2,
            insecure: 0.2, cheerful: -0.2, excited: -0.2, content: 0.1,
            thoughtful: 0.2,
        },
        trigger_situations: [
            'stranger', 'unfamiliar', 'suspicious', 'unknown', 'new place',
            'cautious',
        ],
    },
};

function addMaskFromPreset() {
    const sel = document.getElementById('mask-preset');
    if (!sel || !sel.value) return;
    const preset = MASK_PRESETS[sel.value];
    if (!preset) return;

    fetch('/chat/' + SESSION_ID + '/masks/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preset),
    })
        .then((r) => r.json())
        .then((data) => {
            if (!data.error) location.reload();
            else alert(data.error);
        });
}

function addCustomMask() {
    const name = document.getElementById('new-mask-name');
    if (!name || !name.value.trim()) return;

    const payload = {
        name: name.value.trim(),
        description: (
            document.getElementById('new-mask-desc').value || ''
        ).trim(),
        emotional_modifications: parseMods(
            document.getElementById('new-mask-mods').value
        ),
        trigger_situations: (
            document.getElementById('new-mask-triggers').value || ''
        )
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean),
    };

    fetch('/chat/' + SESSION_ID + '/masks/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    })
        .then((r) => r.json())
        .then((data) => {
            if (!data.error) location.reload();
            else alert(data.error);
        });
}

function deleteMask(maskId) {
    fetch('/chat/' + SESSION_ID + '/masks/' + maskId + '/delete', {
        method: 'POST',
    })
        .then((r) => r.json())
        .then((data) => {
            if (data.ok) {
                const el = document.getElementById('mask-' + maskId);
                if (el) el.remove();
                const badge = document.getElementById('mask-count-badge');
                const list = document.getElementById('mask-list');
                if (badge && list)
                    badge.textContent =
                        '(' + list.querySelectorAll('.mask-item').length + ')';
            }
        });
}

/* ── Trigger Management ── */
function addTrigger() {
    const desc = document.getElementById('new-trigger-desc');
    if (!desc || !desc.value.trim()) return;

    const payload = {
        description: desc.value.trim(),
        trigger_type: document.getElementById('new-trigger-type').value,
        rules: parseRules(document.getElementById('new-trigger-rules').value),
        match_all:
            document.getElementById('new-trigger-matchall').value === 'true',
        keyword_triggers: (
            document.getElementById('new-trigger-keywords').value || ''
        )
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean),
        response_type: 'modifications',
        response_data: parseMods(
            document.getElementById('new-trigger-response').value
        ),
    };

    fetch('/chat/' + SESSION_ID + '/triggers/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    })
        .then((r) => r.json())
        .then((data) => {
            if (!data.error) location.reload();
            else alert(data.error);
        });
}

function toggleTriggerActive(triggerId) {
    fetch('/chat/' + SESSION_ID + '/triggers/' + triggerId + '/toggle', {
        method: 'POST',
    })
        .then((r) => r.json())
        .then((data) => {
            if (!data.error) location.reload();
        });
}

function deleteTrigger(triggerId) {
    fetch('/chat/' + SESSION_ID + '/triggers/' + triggerId + '/delete', {
        method: 'POST',
    })
        .then((r) => r.json())
        .then((data) => {
            if (data.ok) {
                const el = document.getElementById('trig-' + triggerId);
                if (el) el.remove();
                const badge = document.getElementById('trigger-count-badge');
                const list = document.getElementById('trigger-list');
                if (badge && list)
                    badge.textContent =
                        '(' +
                        list.querySelectorAll('.trigger-item').length +
                        ')';
            }
        });
}

/* ── Speaker Profile Toggle ── */
function toggleNewProfile() {
    const sel = document.getElementById('speaker-profile-select');
    const fields = document.getElementById('new-profile-fields');
    const preview = document.getElementById('speaker-profile-preview');
    if (!sel) return;
    if (sel.value === '__new__') {
        if (fields) fields.style.display = 'block';
        if (preview) preview.style.display = 'none';
    } else {
        if (fields) fields.style.display = 'none';
        if (typeof profiles !== 'undefined') {
            const profile = profiles.find((p) => p.id === sel.value);
            if (profile && profile.context && preview) {
                preview.style.display = 'block';
                preview.textContent = profile.context;
            } else if (preview) {
                preview.style.display = 'none';
            }
        }
    }
}
