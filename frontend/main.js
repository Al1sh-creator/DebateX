/* ============================================================
   DebateX — Frontend Application Controller
   ============================================================ */

const API_BASE = '/api';

// ── State ──────────────────────────────────────────────────
let state = {
    token: localStorage.getItem('debatex_token'),
    username: localStorage.getItem('debatex_username'),
    userId: localStorage.getItem('debatex_userId'),
    agents: [],
    currentDebateId: null,
    scores: { a: 0, b: 0 },
    roundScores: [],
};

// ── Init ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initBackground();
    setupEventListeners();
    if (state.token) {
        showScreen('dashboard-screen');
        loadDashboard();
    } else {
        showScreen('auth-screen');
    }
});

// ── Background Animation ───────────────────────────────────
function initBackground() {
    const canvas = document.getElementById('bg-canvas');
    const ctx = canvas.getContext('2d');
    let particles = [];

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    class Particle {
        constructor() {
            this.reset();
        }
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 0.3;
            this.vy = (Math.random() - 0.5) * 0.3;
            this.radius = Math.random() * 1.5 + 0.5;
            this.opacity = Math.random() * 0.5 + 0.1;
        }
        update() {
            this.x += this.vx;
            this.y += this.vy;
            if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
            if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 229, 255, ${this.opacity})`;
            ctx.fill();
        }
    }

    for (let i = 0; i < 60; i++) particles.push(new Particle());

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => { p.update(); p.draw(); });

        // Draw connections
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(0, 229, 255, ${0.06 * (1 - dist / 120)})`;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animate);
    }
    animate();
}

// ── Event Listeners ────────────────────────────────────────
function setupEventListeners() {
    // Auth tabs
    document.getElementById('login-tab-btn').addEventListener('click', () => switchAuthTab('login'));
    document.getElementById('register-tab-btn').addEventListener('click', () => switchAuthTab('register'));

    // Auth forms
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('register-form').addEventListener('submit', handleRegister);

    // Nav
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => switchView(btn.dataset.view));
    });
    document.getElementById('logout-btn').addEventListener('click', handleLogout);

    // Topic chips
    document.querySelectorAll('.topic-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.getElementById('debate-topic').value = chip.dataset.topic;
        });
    });

    // Rounds slider
    document.getElementById('num-rounds').addEventListener('input', (e) => {
        document.getElementById('rounds-display').textContent = e.target.value;
    });

    // Start debate
    document.getElementById('start-debate-btn').addEventListener('click', handleStartDebate);

    // Agent modal
    document.getElementById('create-agent-btn').addEventListener('click', () => {
        document.getElementById('agent-modal').classList.remove('hidden');
    });
    document.getElementById('cancel-agent-btn').addEventListener('click', () => {
        document.getElementById('agent-modal').classList.add('hidden');
    });
    document.getElementById('create-agent-form').addEventListener('submit', handleCreateAgent);

    // Agent sliders
    ['aggression', 'logic', 'emotion', 'evidence'].forEach(name => {
        const el = document.getElementById(`agent-${name}`);
        const valEl = name === 'aggression' ? document.getElementById('aggr-val') :
            name === 'logic' ? document.getElementById('logic-val') :
                name === 'emotion' ? document.getElementById('emotion-val') :
                    document.getElementById('evidence-val');
        el.addEventListener('input', () => valEl.textContent = el.value);
    });

    // Arena back
    document.getElementById('back-to-dashboard-btn').addEventListener('click', () => {
        showScreen('dashboard-screen');
    });
    document.getElementById('new-debate-btn').addEventListener('click', () => {
        document.getElementById('results-overlay').classList.add('hidden');
        showScreen('dashboard-screen');
    });
    document.getElementById('review-debate-btn').addEventListener('click', () => {
        document.getElementById('results-overlay').classList.add('hidden');
    });
}

// ── Screens ────────────────────────────────────────────────
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId).classList.add('active');
}

function switchAuthTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    document.getElementById('login-form').classList.toggle('hidden', tab !== 'login');
    document.getElementById('register-form').classList.toggle('hidden', tab !== 'register');
    document.getElementById('auth-error').classList.add('hidden');
}

function switchView(view) {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelector(`[data-view="${view}"]`).classList.add('active');
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`${view}-view`).classList.add('active');

    if (view === 'agents') loadAgents();
    if (view === 'history') loadHistory();
    if (view === 'leaderboard') loadLeaderboard();
}

// ── API Helper ─────────────────────────────────────────────
async function api(endpoint, options = {}) {
    const headers = { 'Content-Type': 'application/json' };
    if (state.token) headers['Authorization'] = `Bearer ${state.token}`;

    const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

    if (res.status === 401 || res.status === 403) {
        handleLogout();
        throw new Error('Session expired');
    }

    if (!res.ok) {
        const err = await res.json().catch(() => ({ message: 'Request failed' }));
        throw new Error(err.message || `Error ${res.status}`);
    }

    return res.json();
}

// ── Auth Handlers ──────────────────────────────────────────
async function handleLogin(e) {
    e.preventDefault();
    const errEl = document.getElementById('auth-error');
    errEl.classList.add('hidden');

    try {
        const data = await api('/auth/login', {
            method: 'POST',
            body: JSON.stringify({
                username: document.getElementById('login-username').value,
                password: document.getElementById('login-password').value,
            }),
        });
        setAuth(data);
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('hidden');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const errEl = document.getElementById('auth-error');
    errEl.classList.add('hidden');

    try {
        const data = await api('/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                username: document.getElementById('reg-username').value,
                email: document.getElementById('reg-email').value,
                password: document.getElementById('reg-password').value,
            }),
        });
        setAuth(data);
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('hidden');
    }
}

function setAuth(data) {
    state.token = data.token;
    state.username = data.username;
    state.userId = data.userId;
    localStorage.setItem('debatex_token', data.token);
    localStorage.setItem('debatex_username', data.username);
    localStorage.setItem('debatex_userId', data.userId);
    document.getElementById('username-display').textContent = data.username;
    showScreen('dashboard-screen');
    loadDashboard();
}

function handleLogout() {
    state.token = null;
    state.username = null;
    localStorage.removeItem('debatex_token');
    localStorage.removeItem('debatex_username');
    localStorage.removeItem('debatex_userId');
    showScreen('auth-screen');
}

// ── Dashboard ──────────────────────────────────────────────
async function loadDashboard() {
    document.getElementById('username-display').textContent = state.username;
    await loadAgents();
    populateAgentSelects();
}

async function loadAgents() {
    try {
        state.agents = await api('/agents');
        renderAgentGrid();
        populateAgentSelects();
    } catch (err) {
        console.error('Failed to load agents', err);
    }
}

function renderAgentGrid() {
    const grid = document.getElementById('agents-grid');
    if (state.agents.length === 0) {
        grid.innerHTML = `
            <div class="empty-state glass-card" style="grid-column: 1 / -1; padding: 60px;">
                <div class="icon">🤖</div>
                <p>No agents yet. Create your first AI debater!</p>
            </div>`;
        return;
    }
    grid.innerHTML = state.agents.map(a => `
        <div class="agent-card glass-card">
            <div class="card-header">
                <div>
                    <div class="agent-name">${a.name}</div>
                    <span class="persona-tag">${a.persona}</span>
                </div>
                <span class="elo-badge">⭐ ${a.eloRating}</span>
            </div>
            <div class="agent-stats">
                <div class="stat-item">
                    <div class="stat-value" style="color: var(--green);">${a.wins}</div>
                    <div class="stat-label">Wins</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: var(--magenta);">${a.losses}</div>
                    <div class="stat-label">Losses</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${a.draws}</div>
                    <div class="stat-label">Draws</div>
                </div>
            </div>
        </div>
    `).join('');
}

function populateAgentSelects() {
    ['agent-a-select', 'agent-b-select'].forEach(id => {
        const select = document.getElementById(id);
        const current = select.value;
        select.innerHTML = `<option value="">Select Agent...</option>` +
            state.agents.map(a =>
                `<option value="${a.id}">${a.name} (${a.persona} | ELO: ${a.eloRating})</option>`
            ).join('');
        if (current) select.value = current;
    });
}

// ── Create Agent ───────────────────────────────────────────
async function handleCreateAgent(e) {
    e.preventDefault();
    try {
        await api('/agents', {
            method: 'POST',
            body: JSON.stringify({
                name: document.getElementById('agent-name').value,
                persona: document.getElementById('agent-persona').value,
                aggressionLevel: parseFloat(document.getElementById('agent-aggression').value),
                logicWeight: parseFloat(document.getElementById('agent-logic').value),
                emotionWeight: parseFloat(document.getElementById('agent-emotion').value),
                evidencePreference: parseFloat(document.getElementById('agent-evidence').value),
            }),
        });
        document.getElementById('agent-modal').classList.add('hidden');
        document.getElementById('create-agent-form').reset();
        await loadAgents();
    } catch (err) {
        alert('Failed to create agent: ' + err.message);
    }
}

// ── Start Debate ───────────────────────────────────────────
async function handleStartDebate() {
    const topic = document.getElementById('debate-topic').value.trim();
    const agentAId = document.getElementById('agent-a-select').value;
    const agentBId = document.getElementById('agent-b-select').value;
    const numRounds = parseInt(document.getElementById('num-rounds').value);

    if (!topic) return alert('Enter a debate topic');
    if (!agentAId || !agentBId) return alert('Select both agents');
    if (agentAId === agentBId) return alert('Select different agents');

    try {
        const debate = await api('/debates', {
            method: 'POST',
            body: JSON.stringify({
                topic, agentAId: parseInt(agentAId),
                agentBId: parseInt(agentBId), numRounds,
            }),
        });

        state.currentDebateId = debate.id;
        state.scores = { a: 0, b: 0 };
        state.roundScores = [];

        // Setup arena UI
        document.getElementById('arena-topic').textContent = debate.topic;
        document.getElementById('total-rounds').textContent = debate.numRounds;
        document.getElementById('current-round').textContent = '1';
        document.getElementById('arena-agent-a-name').textContent = debate.agentA.name;
        document.getElementById('arena-agent-b-name').textContent = debate.agentB.name;
        document.getElementById('arena-agent-a-persona').textContent = debate.agentA.persona;
        document.getElementById('arena-agent-b-persona').textContent = debate.agentB.persona;
        document.getElementById('score-a').textContent = '0';
        document.getElementById('score-b').textContent = '0';
        document.getElementById('arguments-a').innerHTML = '';
        document.getElementById('arguments-b').innerHTML = '';
        document.getElementById('judge-analysis').innerHTML = '';
        document.getElementById('results-overlay').classList.add('hidden');
        document.getElementById('arena-status').textContent = 'Debate in progress...';

        showScreen('arena-screen');

        // Connect WebSocket
        connectDebateWebSocket(debate.id);

    } catch (err) {
        alert('Failed to start debate: ' + err.message);
    }
}

// ── WebSocket ──────────────────────────────────────────────
function connectDebateWebSocket(debateId) {
    // Using SockJS + STOMP
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/sockjs-client@1.6.1/dist/sockjs.min.js';
    script.onload = () => {
        const script2 = document.createElement('script');
        script2.src = 'https://cdn.jsdelivr.net/npm/@stomp/stompjs@7.0.0/bundles/stomp.umd.min.js';
        script2.onload = () => {
            const sock = new SockJS('/ws/debate');
            const stompClient = new StompJs.Client({
                webSocketFactory: () => sock,
                reconnectDelay: 5000,
            });

            stompClient.onConnect = () => {
                stompClient.subscribe(`/topic/debate/${debateId}`, (msg) => {
                    const data = JSON.parse(msg.body);
                    handleDebateEvent(data);
                });
            };

            stompClient.activate();
        };
        document.head.appendChild(script2);
    };
    document.head.appendChild(script);

    // Fallback: poll for results
    pollDebateStatus(debateId);
}

async function pollDebateStatus(debateId) {
    const poll = setInterval(async () => {
        try {
            const debate = await api(`/debates/${debateId}`);
            if (debate.status === 'COMPLETED') {
                clearInterval(poll);

                // Check if WebSocket already rendered the debate
                const argsA = document.getElementById('arguments-a');
                if (argsA && argsA.children.length > 0) {
                    // WebSocket handled it, just show results if not already shown
                    if (document.getElementById('results-overlay').classList.contains('hidden')) {
                        showResults(debate);
                    }
                    return;
                }

                // WebSocket missed events — render rounds sequentially
                const rounds = await api(`/debates/${debateId}/rounds`);

                for (let i = 0; i < rounds.length; i++) {
                    const r = rounds[i];

                    // Show round banner
                    showRoundBanner(r.roundNumber, debate.numRounds);
                    await sleep(1800);
                    hideRoundBanner();

                    // Agent A typing
                    showTyping('A', document.getElementById('arena-agent-a-name').textContent);
                    await sleep(1500);
                    hideTyping('A');

                    // Agent A speaks
                    addArgument('A', r.agentAArgument, r.agentAStrategy, r.roundNumber);
                    await sleep(2000);

                    // Agent B typing
                    showTyping('B', document.getElementById('arena-agent-b-name').textContent);
                    await sleep(1500);
                    hideTyping('B');

                    // Agent B speaks
                    addArgument('B', r.agentBArgument, r.agentBStrategy, r.roundNumber);
                    await sleep(2000);

                    // Load and show scores for this round
                    document.getElementById('arena-status').textContent = `⚖️ Judging Round ${r.roundNumber}...`;
                    await sleep(1500);

                    const scores = await api(`/debates/${debateId}/scores`);
                    const roundScoresA = scores.filter(s => s.roundNumber === r.roundNumber);
                    if (roundScoresA.length >= 2) {
                        const sA = roundScoresA[0].totalScore;
                        const sB = roundScoresA[1].totalScore;
                        state.scores.a += Math.round(sA || 0);
                        state.scores.b += Math.round(sB || 0);
                        document.getElementById('score-a').textContent = state.scores.a;
                        document.getElementById('score-b').textContent = state.scores.b;
                        state.roundScores.push({ round: r.roundNumber, a: sA, b: sB });
                        showJudgeOverlay(r.roundNumber, sA, sB,
                            roundScoresA[0].feedback || '', roundScoresA[1].feedback || '', '');
                        addJudgeEntry(r.roundNumber, '', sA, sB);
                        drawScoreChart();
                        await sleep(3500);
                        hideJudgeOverlay();
                    }

                    document.getElementById('arena-status').textContent = 'Debate in progress...';
                    await sleep(1000);
                }

                showResults(debate);
            }
        } catch (err) { /* ignore */ }
    }, 3000);

    setTimeout(() => clearInterval(poll), 300000); // Max 5 min
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

function showTyping(bot, name) {
    const el = document.getElementById(`typing-${bot.toLowerCase()}`);
    const label = document.getElementById(`typing-${bot.toLowerCase()}-label`);
    if (label) label.textContent = `${name} is thinking...`;
    el.classList.remove('hidden');

    const container = document.getElementById(`arguments-${bot.toLowerCase()}`);
    if (container) container.scrollTop = container.scrollHeight;
}

function hideTyping(bot) {
    document.getElementById(`typing-${bot.toLowerCase()}`).classList.add('hidden');
}

function showRoundBanner(round, total) {
    const banner = document.getElementById('round-banner');
    document.getElementById('round-banner-text').textContent = `Round ${round}`;
    document.querySelector('.round-banner-sub').textContent =
        round === 1 ? 'Let the debate begin!' :
            round === total ? 'Final round!' : 'Next round starting...';
    banner.classList.remove('hidden');
}

function hideRoundBanner() {
    document.getElementById('round-banner').classList.add('hidden');
}

function showJudgeOverlay(round, scoreA, scoreB, feedbackA, feedbackB, analysis) {
    const overlay = document.getElementById('judge-overlay');
    document.getElementById('judge-overlay-round').textContent = `Round ${round}`;
    document.getElementById('judge-agent-a-name').textContent =
        document.getElementById('arena-agent-a-name').textContent;
    document.getElementById('judge-agent-b-name').textContent =
        document.getElementById('arena-agent-b-name').textContent;
    document.getElementById('judge-score-a').textContent = Math.round(scoreA);
    document.getElementById('judge-score-b').textContent = Math.round(scoreB);
    document.getElementById('judge-feedback-a').textContent = feedbackA || '';
    document.getElementById('judge-feedback-b').textContent = feedbackB || '';
    document.getElementById('judge-overlay-analysis').textContent = analysis || '';
    overlay.classList.remove('hidden');
}

function hideJudgeOverlay() {
    document.getElementById('judge-overlay').classList.add('hidden');
}

function handleDebateEvent(data) {
    const event = data.event;

    switch (event) {
        case 'round_start':
            document.getElementById('current-round').textContent = data.round;
            showRoundBanner(data.round, data.total || parseInt(document.getElementById('total-rounds').textContent));
            // Auto-hide after WebSocket delay
            setTimeout(() => hideRoundBanner(), 1400);
            break;

        case 'typing_start':
            showTyping(data.bot, data.name || `Agent ${data.bot}`);
            document.getElementById('arena-status').textContent =
                `${data.name || 'Agent ' + data.bot} is crafting an argument...`;
            break;

        case 'turn_complete':
            hideTyping(data.bot);
            addArgument(data.bot, data.content, data.strategy, data.round);
            document.getElementById('arena-status').textContent =
                `${data.bot === 'A' ? document.getElementById('arena-agent-a-name').textContent :
                    document.getElementById('arena-agent-b-name').textContent} has spoken.`;
            break;

        case 'judging':
            document.getElementById('arena-status').textContent = `⚖️ Judge is evaluating Round ${data.round}...`;
            break;

        case 'round_scored':
            state.scores.a += Math.round(data.agent_a_total || 0);
            state.scores.b += Math.round(data.agent_b_total || 0);
            document.getElementById('score-a').textContent = state.scores.a;
            document.getElementById('score-b').textContent = state.scores.b;

            state.roundScores.push({
                round: data.round,
                a: data.agent_a_total,
                b: data.agent_b_total,
            });

            // Show judge evaluation overlay
            showJudgeOverlay(
                data.round,
                data.agent_a_total, data.agent_b_total,
                data.feedback_a || '', data.feedback_b || '',
                data.analysis || ''
            );

            addJudgeEntry(data.round, data.analysis, data.agent_a_total, data.agent_b_total);
            drawScoreChart();

            // Auto-hide judge overlay after 3.5 seconds
            setTimeout(() => {
                hideJudgeOverlay();
                document.getElementById('arena-status').textContent = 'Debate in progress...';
            }, 3500);
            break;

        case 'debate_end':
            // Small delay to let judge overlay dismiss first
            setTimeout(() => {
                showResults({
                    winner: data.winner,
                    totalScoreA: data.totalScoreA,
                    totalScoreB: data.totalScoreB,
                    finalVerdict: data.finalVerdict,
                });
            }, 500);
            break;

        case 'error':
            document.getElementById('arena-status').textContent = `❌ Error: ${data.message}`;
            break;
    }
}

function addArgument(bot, content, strategy, round) {
    const container = document.getElementById(`arguments-${bot.toLowerCase()}`);
    const formatStrategy = strategy ? strategy.replace(/_/g, ' ') : '';
    const agentName = document.getElementById(`arena-agent-${bot.toLowerCase()}-name`)?.textContent || `Agent ${bot}`;

    const bubble = document.createElement('div');
    bubble.className = 'argument-bubble';
    bubble.innerHTML = `
        <div class="argument-header">
            <span class="argument-agent-name">${agentName}</span>
            <div class="argument-meta">
                ${formatStrategy ? `<span class="argument-strategy">${formatStrategy}</span>` : ''}
                <span class="argument-round">Round ${round}</span>
            </div>
        </div>
        <p>${content}</p>
    `;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

function addJudgeEntry(round, analysis, scoreA, scoreB) {
    const container = document.getElementById('judge-analysis');
    const entry = document.createElement('div');
    entry.className = 'judge-entry';
    entry.innerHTML = `
        <strong>Round ${round}:</strong>
        <span style="color: var(--cyan)">${Math.round(scoreA)}</span> vs
        <span style="color: var(--magenta)">${Math.round(scoreB)}</span>
        <br><small>${analysis || ''}</small>
    `;
    container.appendChild(entry);
    container.scrollTop = container.scrollHeight;
}

function showResults(debate) {
    const overlay = document.getElementById('results-overlay');
    const announcement = document.getElementById('winner-announcement');

    if (debate.winner === 'TIE') {
        announcement.innerHTML = '🤝 It\'s a Tie!';
        announcement.style.color = 'var(--gold)';
    } else if (debate.winner === 'A' || (debate.agentA && debate.winner === debate.agentA.name)) {
        announcement.innerHTML = '🏆 Agent A Wins!';
        announcement.style.color = 'var(--cyan)';
    } else {
        announcement.innerHTML = '🏆 Agent B Wins!';
        announcement.style.color = 'var(--magenta)';
    }

    document.getElementById('result-agent-a').textContent = document.getElementById('arena-agent-a-name').textContent;
    document.getElementById('result-agent-b').textContent = document.getElementById('arena-agent-b-name').textContent;
    document.getElementById('result-score-a').textContent = debate.totalScoreA;
    document.getElementById('result-score-a').style.color = 'var(--cyan)';
    document.getElementById('result-score-b').textContent = debate.totalScoreB;
    document.getElementById('result-score-b').style.color = 'var(--magenta)';
    document.getElementById('final-verdict').textContent = debate.finalVerdict || '';

    document.getElementById('arena-status').textContent = '✅ Debate Complete';
    overlay.classList.remove('hidden');
}

// ── Score Chart ────────────────────────────────────────────
function drawScoreChart() {
    const canvas = document.getElementById('score-canvas');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (state.roundScores.length === 0) return;

    const padding = 40;
    const w = canvas.width - padding * 2;
    const h = canvas.height - padding * 2;
    const maxScore = Math.max(...state.roundScores.flatMap(s => [s.a, s.b]), 1) * 1.2;

    // Grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = padding + (h / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(padding + w, y);
        ctx.stroke();
    }

    // Lines
    const drawLine = (color, key) => {
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        state.roundScores.forEach((s, i) => {
            const x = padding + (w / Math.max(state.roundScores.length - 1, 1)) * i;
            const y = padding + h - (s[key] / maxScore) * h;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();

        // Dots
        ctx.fillStyle = color;
        state.roundScores.forEach((s, i) => {
            const x = padding + (w / Math.max(state.roundScores.length - 1, 1)) * i;
            const y = padding + h - (s[key] / maxScore) * h;
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        });
    };

    drawLine('#00e5ff', 'a');
    drawLine('#ff006e', 'b');

    // Labels
    ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
    ctx.font = '10px Inter';
    state.roundScores.forEach((s, i) => {
        const x = padding + (w / Math.max(state.roundScores.length - 1, 1)) * i;
        ctx.fillText(`R${s.round}`, x - 6, canvas.height - 8);
    });
}

// ── History ────────────────────────────────────────────────
async function loadHistory() {
    try {
        const debates = await api('/debates');
        const list = document.getElementById('history-list');

        if (debates.length === 0) {
            list.innerHTML = `
                <div class="empty-state">
                    <div class="icon">📜</div>
                    <p>No debates yet. Start your first one!</p>
                </div>`;
            return;
        }

        list.innerHTML = debates.map(d => `
            <div class="history-item glass-card">
                <div>
                    <div class="history-topic">${d.topic}</div>
                    <div class="history-agents">${d.agentA?.name || 'Agent A'} vs ${d.agentB?.name || 'Agent B'}</div>
                </div>
                <div class="history-result">
                    <div class="history-winner" style="color: ${d.isDraw ? 'var(--gold)' : 'var(--green)'}">
                        ${d.isDraw ? '🤝 Tie' : `🏆 ${d.winner}`}
                    </div>
                    <div class="history-score">${d.totalScoreA} — ${d.totalScoreB}</div>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Failed to load history', err);
    }
}

// ── Leaderboard ────────────────────────────────────────────
async function loadLeaderboard() {
    try {
        const rankings = await api('/agents/leaderboard');
        const body = document.getElementById('leaderboard-body');

        if (rankings.length === 0) {
            body.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 40px;">No rankings yet</td></tr>`;
            return;
        }

        body.innerHTML = rankings.map((r, i) => `
            <tr>
                <td class="${i < 3 ? `rank-${i + 1}` : ''}">#${r.rank || i + 1}</td>
                <td><strong>${r.agentName}</strong></td>
                <td><span class="persona-tag">${r.persona}</span></td>
                <td class="elo-badge">${r.eloRating}</td>
                <td>${r.totalDebates}</td>
                <td>${r.winRate?.toFixed(1) || 0}%</td>
                <td>${r.avgScore?.toFixed(1) || 0}</td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load leaderboard', err);
    }
}
