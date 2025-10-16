document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = 'http://127.0.0.1:8000';

    // --- DOM Elements ---
    const authContainer = document.getElementById('auth-container');
    const appContainer = document.getElementById('app-container');
    const loginView = document.getElementById('login-view');
    const registerView = document.getElementById('register-view');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const showRegisterLink = document.getElementById('show-register');
    const showLoginLink = document.getElementById('show-login');
    const logoutBtn = document.getElementById('logout-btn');
    const userNameDisplay = document.getElementById('user-name-display');
    const sourcesList = document.getElementById('sourcesList');
    const urlInput = document.getElementById('urlInput');
    const pdfInput = document.getElementById('pdfInput');
    const processBtn = document.getElementById('processBtn');
    const welcomeScreen = document.getElementById('welcome-screen');
    const chatInterface = document.getElementById('chat-interface');
    const chatHeader = document.getElementById('chat-header');
    const chatHistory = document.getElementById('chat-history');
    const chatInput = document.getElementById('chatInput');
    const chatBtn = document.getElementById('chatBtn');
    const spinnerOverlay = document.getElementById('spinner-overlay');

    // --- App State ---
    let currentUser = null;
    let activeSource = null;

    // --- API Functions ---
    const api = {
        register: (name, email, password) => handleFetch('/register', { method: 'POST', body: { name, email, password } }),
        login: (email, password) => handleFetch('/login', { method: 'POST', body: { email, password } }),
        getSources: (userId) => handleFetch(`/sources/${userId}`),
        processUrl: (url, user_id) => handleFetch('/process-source', { method: 'POST', body: { url, user_id } }),
        processPdf: (file, user_id) => {
            const formData = new FormData();
            formData.append('file', file);
            return handleFetch(`/process-pdf-upload/${user_id}`, { method: 'POST', body: formData, isFormData: true });
        },
        deleteSource: (sourceId, userId) => handleFetch(`/sources/${sourceId}/${userId}`, { method: 'DELETE' }),
        chat: (source_identifier, question, user_id) => handleFetch('/chat', { method: 'POST', body: { source_identifier, question, user_id } }),
    };

    async function handleFetch(endpoint, options = {}) {
        const { method = 'GET', body = null, isFormData = false } = options;
        const config = {
            method,
            headers: {},
        };
        if (body) {
            if (isFormData) {
                config.body = body;
            } else {
                config.headers['Content-Type'] = 'application/json';
                config.body = JSON.stringify(body);
            }
        }
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'An API error occurred.');
        }
        return response.json();
    }

    // --- Auth Logic ---
    function setupAuth() {
        showRegisterLink.addEventListener('click', (e) => {
            e.preventDefault();
            loginView.classList.add('hidden');
            registerView.classList.remove('hidden');
        });
        showLoginLink.addEventListener('click', (e) => {
            e.preventDefault();
            registerView.classList.add('hidden');
            loginView.classList.remove('hidden');
        });
        loginForm.addEventListener('submit', handleLogin);
        registerForm.addEventListener('submit', handleRegister);
        logoutBtn.addEventListener('click', handleLogout);
    }

    async function handleLogin(e) {
        e.preventDefault();
        showSpinner();
        try {
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;
            const user = await api.login(email, password);
            initializeApp(user);
        } catch (error) {
            alert(`Login Failed: ${error.message}`);
        } finally {
            hideSpinner();
        }
    }

    async function handleRegister(e) {
        e.preventDefault();
        showSpinner();
        try {
            const name = document.getElementById('register-name').value;
            const email = document.getElementById('register-email').value;
            const password = document.getElementById('register-password').value;
            const user = await api.register(name, email, password);
            initializeApp(user);
        } catch (error) {
            alert(`Registration Failed: ${error.message}`);
        } finally {
            hideSpinner();
        }
    }

    function handleLogout() {
        currentUser = null;
        sessionStorage.removeItem('cognicoreUser');
        authContainer.classList.remove('hidden');
        appContainer.classList.add('hidden');
    }

    // --- Main App Logic ---
    function initializeApp(user) {
        currentUser = user;
        sessionStorage.setItem('cognicoreUser', JSON.stringify(user));
        authContainer.classList.add('hidden');
        appContainer.classList.remove('hidden');
        userNameDisplay.textContent = user.name;
        loadSources();
        resetToWelcome();
    }

    async function loadSources() {
        if (!currentUser) return;
        const sources = await api.getSources(currentUser.id);
        sourcesList.innerHTML = '';
        sources.forEach(source => {
            const div = document.createElement('div');
            div.className = 'source-item';
            div.dataset.sourceId = source.id;
            div.innerHTML = `
                <div>
                    <h3>${source.title || 'Untitled'}</h3>
                    <p>${source.source_identifier}</p>
                </div>
                <div class="actions">
                    <button class="delete-btn" title="Delete">&times;</button>
                </div>
            `;
            div.addEventListener('click', () => selectSource(source));
            div.querySelector('.delete-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                handleDeleteSource(source.id);
            });
            sourcesList.appendChild(div);
        });
    }

    async function handleProcess() {
        const url = urlInput.value.trim();
        const pdfFile = pdfInput.files[0];
        if (!url && !pdfFile) return;

        showSpinner();
        try {
            const result = url
                ? await api.processUrl(url, currentUser.id)
                : await api.processPdf(pdfFile, currentUser.id);
            
            await loadSources();
            selectSource(result);
            urlInput.value = '';
            pdfInput.value = '';
        } catch (error) {
            alert(`Processing Failed: ${error.message}`);
        } finally {
            hideSpinner();
        }
    }

    async function handleDeleteSource(sourceId) {
        if (!confirm("Are you sure?")) return;
        showSpinner();
        try {
            await api.deleteSource(sourceId, currentUser.id);
            await loadSources();
            if (activeSource && activeSource.id === sourceId) {
                resetToWelcome();
            }
        } catch (error) {
            alert(`Delete Failed: ${error.message}`);
        } finally {
            hideSpinner();
        }
    }

    function selectSource(source) {
        activeSource = source;
        // Highlight active source
        document.querySelectorAll('.source-item').forEach(el => el.classList.remove('active'));
        document.querySelector(`[data-source-id='${source.id}']`).classList.add('active');

        welcomeScreen.classList.add('hidden');
        chatInterface.classList.remove('hidden');
        chatHeader.textContent = `Chat with: ${source.title || source.source_identifier}`;
        chatHistory.innerHTML = '';
        addMessageToChat('ai', 'Content selected. Ask me anything!');
    }

    async function handleChat() {
        if (!activeSource) return;
        const question = chatInput.value.trim();
        if (!question) return;

        addMessageToChat('user', question);
        chatInput.value = '';
        const thinkingBubble = addMessageToChat('ai', '...');

        try {
            const response = await api.chat(activeSource.source_identifier, question, currentUser.id);
            thinkingBubble.textContent = response.answer;
        } catch (error) {
            thinkingBubble.textContent = `Error: ${error.message}`;
        }
    }

    // --- UI Helpers ---
    function showSpinner() { spinnerOverlay.classList.remove('hidden'); }
    function hideSpinner() { spinnerOverlay.classList.add('hidden'); }

    function resetToWelcome() {
        activeSource = null;
        welcomeScreen.classList.remove('hidden');
        chatInterface.classList.add('hidden');
        document.querySelectorAll('.source-item').forEach(el => el.classList.remove('active'));
    }

    function addMessageToChat(sender, text) {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${sender}`;
        bubble.textContent = text;
        chatHistory.appendChild(bubble);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        return bubble;
    }

    // --- Initial Load & Event Listeners ---
    const savedUser = sessionStorage.getItem('cognicoreUser');
    if (savedUser) {
        initializeApp(JSON.parse(savedUser));
    }
    setupAuth();
    processBtn.addEventListener('click', handleProcess);
    chatBtn.addEventListener('click', handleChat);
    chatInput.addEventListener('keypress', e => { if (e.key === 'Enter') handleChat(); });
});
