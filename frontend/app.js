// Configuration
const API_BASE = "http://localhost:8000/api";
const CONNECTION_CHECK_INTERVAL = 30000; // 30 seconds

// DOM Elements
const elements = {
    fileUpload: document.getElementById('file-upload'),
    fileNameDisplay: document.getElementById('file-name'),
    dropZone: document.getElementById('drop-zone'),
    languageForm: document.getElementById('language-form'),
    uploadForm: document.getElementById('upload-form'),
    languageSelect: document.getElementById('language-select'),
    languageGrid: document.getElementById('language-grid'),
    toast: document.getElementById('toast'),
    toastMessage: document.getElementById('toast-message'),
    connectionStatus: document.getElementById('connection-status'),
    statusIndicator: document.querySelector('.status-indicator'),
    uploadMessage: document.getElementById('upload-message'),
    duplicateMessage: document.getElementById('duplicate-message'),
    selectMessage: document.getElementById('select-message'),
    selectMoMessage: document.getElementById('select-mo-message'),
    moMessage: document.getElementById('mo-message')
};

// State
const state = {
    connectionCheckInterval: null
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    initFileUpload();
    initDragAndDrop();
    initForms();
    loadLanguages();
    startConnectionMonitor();
    
    // Add some demo data for UI preview
    populateDemoLanguages();
});

// Initialize file upload display
function initFileUpload() {
    elements.fileUpload.addEventListener('change', function() {
        elements.fileNameDisplay.textContent = this.files.length 
            ? this.files[0].name 
            : 'No file selected';
    });
}

// Initialize drag and drop functionality
function initDragAndDrop() {
    const handleDrag = (e) => {
        e.preventDefault();
        elements.dropZone.style.borderColor = '#4361ee';
        elements.dropZone.style.backgroundColor = 'rgba(67, 97, 238, 0.05)';
    };

    elements.dropZone.addEventListener('dragover', handleDrag);
    
    elements.dropZone.addEventListener('dragleave', () => {
        elements.dropZone.style.borderColor = '#dee2e6';
        elements.dropZone.style.backgroundColor = '#fafbfc';
    });
    
    elements.dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.dropZone.style.borderColor = '#dee2e6';
        elements.dropZone.style.backgroundColor = '#fafbfc';
        
        if (e.dataTransfer.files.length) {
            elements.fileUpload.files = e.dataTransfer.files;
            elements.fileNameDisplay.textContent = e.dataTransfer.files[0].name;
        }
    });
}

// Initialize form submissions
function initForms() {
    elements.languageForm.addEventListener('submit', handleLanguageSubmit);
    elements.uploadForm.addEventListener('submit', handleFileUpload);
    document.getElementById('select-btn').addEventListener('click', handleGeneratePO);
    document.getElementById('mo-btn').addEventListener('click', handleGenerateMO);
}

// API Connection Monitoring
function startConnectionMonitor() {
    checkApiConnection();
    state.connectionCheckInterval = setInterval(checkApiConnection, CONNECTION_CHECK_INTERVAL);
}

function updateConnectionStatus(isConnected) {
    if (isConnected) {
        elements.connectionStatus.textContent = 'Connected to API';
        elements.statusIndicator.classList.remove('status-disconnected');
        elements.statusIndicator.classList.add('status-connected');
    } else {
        elements.connectionStatus.textContent = 'API Connection Lost';
        elements.statusIndicator.classList.remove('status-connected');
        elements.statusIndicator.classList.add('status-disconnected');
    }
}

// Language Management
async function loadLanguages() {
    try {
        elements.languageSelect.innerHTML = '<option value="">Loading languages...</option>';
        const response = await axios.get(`${API_BASE}/get_all_languages`);
        const languages = response.data;
        
        elements.languageSelect.innerHTML = languages.length 
            ? '<option value="">Select a language</option>'
            : '<option value="">No languages available</option>';
        
        languages.forEach(lang => {
            const option = document.createElement('option');
            option.value = lang;
            option.textContent = lang;
            elements.languageSelect.appendChild(option);
        });
        
        updateLanguageGrid(languages);
        showToast('Languages loaded successfully', 'success');
    } catch (error) {
        showToast('Error loading languages. Please try again.', 'error');
    }
}

function updateLanguageGrid(languages) {
    elements.languageGrid.innerHTML = '';
    
    languages.forEach(lang => {
        const card = document.createElement('div');
        card.className = 'language-card';
        card.dataset.lang = lang;
        card.innerHTML = `
            <i class="fas fa-flag"></i>
            <h3>${lang}</h3>
            <p>${lang.split('_')[0]}</p>
        `;
        card.addEventListener('click', () => {
            elements.languageSelect.value = lang;
            showToast(`Selected ${lang}`, 'info');
        });
        elements.languageGrid.appendChild(card);
    });
}

// Form Handlers
async function handleLanguageSubmit(e) {
    e.preventDefault();
    
    const btn = document.getElementById('add-language-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<div class="loading"></div> Processing...';
    btn.disabled = true;
    
    const language = {
        language: document.getElementById('name').value.trim(),
        language_code: document.getElementById('lang-string').value.trim(),
        language_name: document.getElementById('display-name').value.trim()
    };
    
    try {
        await axios.post(`${API_BASE}/add-language`, language);
        showToast('Language added successfully', 'success');
        e.target.reset();
        await loadLanguages();
    } catch (error) {
        const msg = error.response?.data?.detail || 'Error adding language';
        showToast(msg, 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

async function handleFileUpload(e) {
    e.preventDefault();
    const btn = document.getElementById('upload-btn');
    
    if (!elements.fileUpload.files.length) {
        setStatusMessage(elements.uploadMessage, 'Please select a file first', 'warning');
        return;
    }

    const originalText = btn.innerHTML;
    btn.innerHTML = '<div class="loading"></div> Uploading...';
    btn.disabled = true;
    
    const file = elements.fileUpload.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await axios.post(`${API_BASE}/upload`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        setStatusMessage(elements.uploadMessage, res.data.message, 'success');
        elements.fileUpload.value = '';
        elements.fileNameDisplay.textContent = 'No file selected';

        // Updated to handle skipped list
        displaySkippedList(elements.duplicateMessage, res.data.skipped, 'error');

    } catch (error) {
        const msg = error.response?.data?.detail || 'Error uploading file';
        setStatusMessage(elements.uploadMessage, msg, 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// New function to display skipped items
function displaySkippedList(element, items, type) {
    element.innerHTML = ''; // Clear existing content
    element.className = `list-message ${type}`;

    if (!items || items.length === 0) return;

    const heading = document.createElement('div');
    heading.className = 'list-heading';
    heading.textContent = 'Skipped values:';
    element.appendChild(heading);

    const list = document.createElement('ul');
    list.className = 'list-items';
    
    items.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        list.appendChild(li);
    });

    element.appendChild(list);
}

async function handleGeneratePO() {
    const lang = elements.languageSelect.value;
    const btn = document.getElementById('select-btn');
    
    if (!lang) {
        setStatusMessage(elements.selectMessage, 'Please select a language first', 'warning');
        return;
    }

    const originalText = btn.innerHTML;
    btn.innerHTML = '<div class="loading"></div> Generating...';
    btn.disabled = true;
    clearStatusMessage(elements.selectMessage);

    try {
        const response = await axios.post(`${API_BASE}/generate-po/${lang}`);
        setStatusMessage(elements.selectMessage, response.data.message, 'success');
    } catch (error) {
        const msg = error.response?.data?.detail || 'Error generating PO file';
        setStatusMessage(elements.selectMessage, msg, 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

async function handleGenerateMO() {
    const lang = elements.languageSelect.value;
    const btn = document.getElementById('mo-btn');
    
    if (!lang) {
        setStatusMessage(elements.selectMoMessage, 'Please select a language first', 'warning');
        return;
    }

    const originalText = btn.innerHTML;
    btn.innerHTML = '<div class="loading"></div> Generating...';
    btn.disabled = true;
    clearStatusMessage(elements.selectMoMessage);
    clearStatusMessage(elements.moMessage);

    try {
        const response = await axios.post(`${API_BASE}/localization/compile-po/${lang}`);
        setStatusMessage(elements.selectMoMessage, response.data.message, 'success');
    } catch (error) {
        let msg = error.response?.data?.detail || 'Error generating MO file';
        
        // Clear any previous content
        elements.moMessage.innerHTML = '';
        elements.moMessage.className = 'mo-message error';
        
        if (msg.includes('\n')) {
            // Create bullet list for multi-line errors
            const ul = document.createElement('ul');
            ul.className = 'error-list';
            
            msg.split('\n')
                .filter(line => line.trim() !== '')
                .forEach(line => {
                    const li = document.createElement('li');
                    li.textContent = line;
                    ul.appendChild(li);
                });

            elements.moMessage.appendChild(ul);
        } else {
            // Handle single-line errors
            elements.moMessage.textContent = msg;
        }
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// UI Utilities
function showToast(message, type) {
    const iconMap = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };

    elements.toast.querySelector('i').className = `fas ${iconMap[type] || 'fa-info-circle'}`;
    elements.toastMessage.textContent = message;
    elements.toast.className = `toast ${type}`;
    
    clearTimeout(elements.toast.timeout);
    setTimeout(() => elements.toast.classList.add('show'), 10);
    
    elements.toast.timeout = setTimeout(() => {
        elements.toast.classList.remove('show');
    }, 5000);
}

function setStatusMessage(element, message, type) {
    element.textContent = message;
    element.className = `status-message ${type}`;
}

function clearStatusMessage(element) {
    element.textContent = '';
    element.className = 'status-message';
}

// For demo purposes only - to be removed in production
function populateDemoLanguages() {
    const languages = ['en_US', 'fr_FR', 'de_DE', 'es_ES', 'ja_JP'];
    const grid = document.getElementById('language-grid');
    
    languages.forEach(lang => {
        const card = document.createElement('div');
        card.className = 'language-card';
        card.dataset.lang = lang;
        card.innerHTML = `
            <i class="fas fa-flag"></i>
            <h3>${lang}</h3>
            <p>${lang.split('_')[0]}</p>
        `;
        grid.appendChild(card);
    });
}