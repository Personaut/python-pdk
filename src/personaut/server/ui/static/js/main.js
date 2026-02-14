/**
 * Personaut Main JavaScript
 * Handles WebSocket connections, UI interactions, and real-time updates.
 */

// WebSocket connection management
class PersonautWebSocket {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.listeners = {};
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/ws/${this.sessionId}`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.emit('connected');
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (e) {
                console.error('Failed to parse WebSocket message:', e);
            }
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.emit('disconnected');
            this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.emit('error', error);
        };
    }

    handleMessage(data) {
        const type = data.type || 'unknown';
        this.emit(type, data);
        this.emit('message', data);
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting... attempt ${this.reconnectAttempts}`);
            setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
        }
    }

    send(type, payload = {}) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, ...payload }));
        }
    }

    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    emit(event, data) {
        const callbacks = this.listeners[event] || [];
        callbacks.forEach(cb => cb(data));
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Emotion visualization
function updateEmotionBar(emotionName, value) {
    const bar = document.querySelector(`[data-emotion="${emotionName}"] .emotion-fill`);
    if (bar) {
        bar.style.width = `${value * 100}%`;
    }
    const percent = document.querySelector(`[data-emotion="${emotionName}"] .emotion-percent`);
    if (percent) {
        percent.textContent = `${Math.round(value * 100)}%`;
    }
}

// Range input value display
function initRangeInputs() {
    document.querySelectorAll('input[type="range"]').forEach(input => {
        const valueDisplay = input.nextElementSibling;
        if (valueDisplay && valueDisplay.classList.contains('range-value')) {
            input.addEventListener('input', () => {
                valueDisplay.textContent = `${input.value}%`;
            });
        }
    });
}

// Search and filter functionality
function initSearchFilter() {
    const searchInput = document.getElementById('search');
    const typeFilter = document.getElementById('type-filter');

    if (searchInput) {
        searchInput.addEventListener('input', filterCards);
    }
    if (typeFilter) {
        typeFilter.addEventListener('change', filterCards);
    }
}

function filterCards() {
    const searchTerm = (document.getElementById('search')?.value || '').toLowerCase();
    const typeValue = document.getElementById('type-filter')?.value || '';

    document.querySelectorAll('.individual-card, .situation-card').forEach(card => {
        const name = card.querySelector('h3')?.textContent.toLowerCase() || '';
        const type = card.dataset.type || '';

        const matchesSearch = name.includes(searchTerm);
        const matchesType = !typeValue || type === typeValue;

        card.style.display = matchesSearch && matchesType ? '' : 'none';
    });
}

// Chat functionality
function initChat(sessionId) {
    const messagesContainer = document.getElementById('messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.querySelector('[onclick*="sendMessage"]');

    if (!messagesContainer || !messageInput) return;

    // Initialize WebSocket
    const ws = new PersonautWebSocket(sessionId);

    ws.on('new_message', (data) => {
        addMessage(data.content, data.sender_name, data.sender_id ? 'received' : 'sent');
    });

    ws.on('emotional_state_change', (data) => {
        console.log('Emotional state changed:', data);
        // Update emotion displays if visible
    });

    ws.connect();

    // Handle sending messages
    window.sendMessage = async function (sessionId) {
        const content = messageInput.value.trim();
        if (!content) return;

        // Add message to UI immediately
        addMessage(content, 'You', 'sent');
        messageInput.value = '';

        // Send via WebSocket
        ws.send('message', { content, sender: 'You' });
    };
}

function addMessage(content, sender, type) {
    const messagesContainer = document.getElementById('messages');
    if (!messagesContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const senderDiv = document.createElement('div');
    senderDiv.className = 'message-sender';
    senderDiv.textContent = sender;

    messageDiv.appendChild(senderDiv);
    messageDiv.appendChild(document.createTextNode(content));

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Modality tab switching
function initModalityTabs() {
    document.querySelectorAll('.modality-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.modality-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Could switch chat interface style here
            const modality = tab.textContent.trim();
            console.log('Switched to modality:', modality);
        });
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initRangeInputs();
    initSearchFilter();
    initModalityTabs();

    // Initialize chat if on chat page — but only if the dedicated chat.js
    // isn't loaded (it defines a superior fetch-based sendMessage).
    // chat.js is loaded by chat_session.html; the simpler text_message.html
    // and in_person.html templates rely on this WebSocket-based fallback.
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer && typeof window.sendMessage !== 'function') {
        const sessionId = window.location.pathname.split('/').pop();
        if (sessionId && sessionId !== 'chat') {
            initChat(sessionId);
        }
    }
});

// Utility functions
function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
