/**
 * Salesplay Language Manager
 * Version: 2.0
 * Clean, organized, and optimized JavaScript
 */

// ===========================
// Configuration
// ===========================
const CONFIG = {
    API_BASE: "http://localhost:8000/api",
    CONNECTION_CHECK_INTERVAL: 30000, // 30 seconds
    TOAST_DURATION: 5000,
    DEBOUNCE_DELAY: 300,
    FILE_SIZE_LIMIT: 10 * 1024 * 1024, // 10MB
};

// ===========================
// DOM Elements Cache
// ===========================
const DOM = {
    // Forms
    forms: {
        language: document.getElementById('language-form'),
        upload: document.getElementById('upload-form'),
        excelUpload: document.getElementById('upload-excel'),
    },
    
    // File Upload Elements
    fileUpload: {
        textInput: document.getElementById('file-upload'),
        excelInput: document.getElementById('excel-file-upload'),
        textDisplay: document.getElementById('file-name'),
        excelDisplay: document.getElementById('excel-file-name'),
        textDropZone: document.getElementById('drop-zone'),
        excelDropZone: document.getElementById('drop-zone-excel'),
    },
    
    // Language Form Inputs
    languageInputs: {
        name: document.getElementById('name'),
        langString: document.getElementById('lang-string'),
        displayName: document.getElementById('display-name'),
    },
    
    // Selects
    selects: {
        language: document.getElementById('language-select'),
        languageExcel: document.getElementById('language-select-excel'),
    },
    
    // Buttons
    buttons: {
        addLanguage: document.getElementById('add-language-btn'),
        upload: document.getElementById('upload-btn'),
        selectPO: document.getElementById('select-btn'),
        selectMO: document.getElementById('mo-btn'),
        downloadExcel: document.getElementById('download-excel-btn'),
        uploadExcel: document.getElementById('excel-upload-btn'),
    },
    
    // Messages
    messages: {
        upload: document.getElementById('upload-message'),
        duplicate: document.getElementById('duplicate-message'),
        selectPO: document.getElementById('select-message'),
        selectMO: document.getElementById('select-mo-message'),
        mo: document.getElementById('mo-message'),
        excelUpload: document.getElementById('excel-upload-message'),
        downloadStatus: document.getElementById('download-status-message'),
    },
    
    // UI Elements
    ui: {
        languageGrid: document.getElementById('language-grid'),
        toast: document.getElementById('toast'),
        toastMessage: document.getElementById('toast-message'),
        connectionStatus: document.getElementById('connection-status'),
        statusIndicator: document.querySelector('.status-indicator'),
    },
};

// ===========================
// Application State
// ===========================
const AppState = {
    connectionCheckInterval: null,
    isConnected: true,
    languages: [],
    currentToastTimeout: null,
};

// ===========================
// API Service
// ===========================
const API = {
    /**
     * Generic API request handler
     */
    async request(url, options = {}) {
        try {
            const response = await axios({
                url: `${CONFIG.API_BASE}${url}`,
                ...options,
            });
            return response;
        } catch (error) {
            console.error(`API Error: ${url}`, error);
            throw error;
        }
    },
    
    /**
     * Check API connection
     */
    async checkConnection() {
        try {
            await axios.get(`${CONFIG.API_BASE}/health`, { timeout: 5000 });
            return true;
        } catch {
            return false;
        }
    },
    
    /**
     * Language endpoints
     */
    languages: {
        getAll: () => API.request('/get_all_languages'),
        add: (data) => API.request('/add-language', { method: 'POST', data }),
    },
    
    /**
     * File endpoints
     */
    files: {
        uploadText: (formData) => 
            API.request('/upload', {
                method: 'POST',
                data: formData,
                headers: { 'Content-Type': 'multipart/form-data' },
            }),
        
        uploadExcel: (lang, formData) => 
            API.request(`/excel-import/${lang}`, {
                method: 'POST',
                data: formData,
                headers: { 'Content-Type': 'multipart/form-data' },
            }),
        
        generatePO: (lang) => 
            API.request(`/generate-po/${lang}`, { method: 'POST' }),
        
        generateMO: (lang) => 
            API.request(`/localization/compile-po/${lang}`, { method: 'POST' }),
    },
};

// ===========================
// UI Utilities
// ===========================
const UI = {
    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const { toast, toastMessage } = DOM.ui;
        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle',
        };
        
        // Clear existing timeout
        if (AppState.currentToastTimeout) {
            clearTimeout(AppState.currentToastTimeout);
        }
        
        // Update toast content
        toast.querySelector('i').className = `fas ${iconMap[type] || iconMap.info}`;
        toastMessage.textContent = message;
        toast.className = `toast ${type}`;
        
        // Show toast
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // Auto-hide after duration
        AppState.currentToastTimeout = setTimeout(() => {
            toast.classList.remove('show');
        }, CONFIG.TOAST_DURATION);
    },
    
    /**
     * Set status message
     */
    setStatusMessage(element, message, type = 'info') {
        if (!element) return;
        element.textContent = message;
        element.className = `status-message ${type}`;
    },
    
    /**
     * Clear status message
     */
    clearStatusMessage(element) {
        if (!element) return;
        element.textContent = '';
        element.className = 'status-message';
    },
    
    /**
     * Display list of items (e.g., skipped items)
     */
    displayList(element, items, type = 'error', heading = 'Items:') {
        if (!element) return;
        
        element.innerHTML = '';
        element.className = `list-message ${type}`;
        
        if (!items || items.length === 0) return;
        
        const headingEl = document.createElement('div');
        headingEl.className = 'list-heading';
        headingEl.textContent = heading;
        element.appendChild(headingEl);
        
        const list = document.createElement('ul');
        list.className = 'list-items';
        
        items.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            list.appendChild(li);
        });
        
        element.appendChild(list);
    },
    
    /**
     * Display error list
     */
    displayErrorList(element, message) {
        if (!element) return;
        
        element.innerHTML = '';
        element.className = 'error-message error';
        
        if (message.includes('\n')) {
            const ul = document.createElement('ul');
            ul.className = 'error-list';
            
            message.split('\n')
                .filter(line => line.trim())
                .forEach(line => {
                    const li = document.createElement('li');
                    li.textContent = line;
                    ul.appendChild(li);
                });
            
            element.appendChild(ul);
        } else {
            element.textContent = message;
        }
    },
    
    /**
     * Set button loading state
     */
    setButtonLoading(button, isLoading, loadingText = 'Processing...') {
        if (!button) return;
        
        if (isLoading) {
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = `<div class="loading"></div> ${loadingText}`;
            button.disabled = true;
        } else {
            button.innerHTML = button.dataset.originalText || button.innerHTML;
            button.disabled = false;
        }
    },
    
    /**
     * Update connection status display
     */
    updateConnectionStatus(isConnected) {
        const { connectionStatus, statusIndicator } = DOM.ui;
        
        AppState.isConnected = isConnected;
        
        if (isConnected) {
            connectionStatus.textContent = 'Connected to API';
            statusIndicator.classList.remove('status-disconnected');
            statusIndicator.classList.add('status-connected');
        } else {
            connectionStatus.textContent = 'API Connection Lost';
            statusIndicator.classList.remove('status-connected');
            statusIndicator.classList.add('status-disconnected');
        }
    },
};

// ===========================
// Language Management
// ===========================
const LanguageManager = {
    /**
     * Load all languages
     */
    async loadLanguages() {
        try {
            const response = await API.languages.getAll();
            const languages = response.data;
            
            AppState.languages = languages;
            
            this.updateSelects(languages);
            this.updateGrid(languages);
            
            UI.showToast('Languages loaded successfully', 'success');
        } catch (error) {
            UI.showToast('Error loading languages. Please try again.', 'error');
            console.error('Load languages error:', error);
        }
    },
    
    /**
     * Update language select dropdowns
     */
    updateSelects(languages) {
        const { language, languageExcel } = DOM.selects;
        
        const createOptions = (selectElement) => {
            selectElement.innerHTML = languages.length
                ? '<option value="">Select a language</option>'
                : '<option value="">No languages available</option>';
            
            languages.forEach(lang => {
                const option = document.createElement('option');
                option.value = lang;
                option.textContent = lang;
                selectElement.appendChild(option);
            });
        };
        
        createOptions(language);
        createOptions(languageExcel);
    },
    
    /**
     * Update language grid display
     */
    updateGrid(languages) {
        const { languageGrid } = DOM.ui;
        
        languageGrid.innerHTML = '';
        
        languages.forEach(lang => {
            const card = document.createElement('div');
            card.className = 'language-card';
            card.dataset.lang = lang;
            
            const flagIcon = this.getFlagIcon(lang);
            const displayName = this.getDisplayName(lang);
            
            card.innerHTML = `
                <i class="fas ${flagIcon}"></i>
                <h3>${lang}</h3>
                <p>${displayName}</p>
            `;
            
            card.addEventListener('click', () => {
                DOM.selects.language.value = lang;
                UI.showToast(`Selected ${lang}`, 'info');
            });
            
            languageGrid.appendChild(card);
        });
    },
    
    /**
     * Get appropriate flag icon for language
     */
    getFlagIcon(lang) {
        const iconMap = {
            'en': 'fa-flag-usa',
            'fr': 'fa-flag',
            'es': 'fa-flag',
            'de': 'fa-flag',
            'it': 'fa-flag',
            'ja': 'fa-flag',
            'zh': 'fa-flag',
        };
        
        const langCode = lang.split('_')[0].toLowerCase();
        return iconMap[langCode] || 'fa-flag';
    },
    
    /**
     * Get display name for language
     */
    getDisplayName(lang) {
        const nameMap = {
            'en_US': 'English (US)',
            'en_GB': 'English (UK)',
            'fr_FR': 'French (France)',
            'es_ES': 'Spanish (Spain)',
            'de_DE': 'German (Germany)',
            'it_IT': 'Italian (Italy)',
            'ja_JP': 'Japanese (Japan)',
            'zh_CN': 'Chinese (China)',
        };
        
        return nameMap[lang] || lang.split('_')[0].toUpperCase();
    },
};

// ===========================
// File Upload Handlers
// ===========================
const FileHandlers = {
    /**
     * Initialize file upload functionality
     */
    init() {
        this.initTextUpload();
        this.initExcelUpload();
        this.initDragAndDrop();
    },
    
    /**
     * Initialize text file upload
     */
    initTextUpload() {
        const { textInput, textDisplay } = DOM.fileUpload;
        
        textInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            textDisplay.textContent = file ? file.name : 'No file selected';
        });
    },
    
    /**
     * Initialize Excel file upload
     */
    initExcelUpload() {
        const { excelInput, excelDisplay } = DOM.fileUpload;
        
        excelInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            excelDisplay.textContent = file ? file.name : 'No file selected';
        });
    },
    
    /**
     * Initialize drag and drop
     */
    initDragAndDrop() {
        this.setupDropZone(DOM.fileUpload.textDropZone, DOM.fileUpload.textInput, DOM.fileUpload.textDisplay);
        this.setupDropZone(DOM.fileUpload.excelDropZone, DOM.fileUpload.excelInput, DOM.fileUpload.excelDisplay);
    },
    
    /**
     * Setup individual drop zone
     */
    setupDropZone(dropZone, fileInput, fileDisplay) {
        if (!dropZone) return;
        
        ['dragover', 'dragenter'].forEach(event => {
            dropZone.addEventListener(event, (e) => {
                e.preventDefault();
                dropZone.classList.add('drag-over');
            });
        });
        
        ['dragleave', 'drop'].forEach(event => {
            dropZone.addEventListener(event, (e) => {
                e.preventDefault();
                dropZone.classList.remove('drag-over');
            });
        });
        
        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                fileDisplay.textContent = files[0].name;
            }
        });
    },
};

// ===========================
// Form Handlers
// ===========================
const FormHandlers = {
    /**
     * Handle language form submission
     */
    async handleLanguageSubmit(e) {
        e.preventDefault();
        
        const button = DOM.buttons.addLanguage;
        UI.setButtonLoading(button, true, 'Adding Language...');
        
        const formData = {
            language: DOM.languageInputs.name.value.trim(),
            language_code: DOM.languageInputs.langString.value.trim(),
            language_name: DOM.languageInputs.displayName.value.trim(),
        };
        
        try {
            await API.languages.add(formData);
            UI.showToast('Language added successfully', 'success');
            e.target.reset();
            await LanguageManager.loadLanguages();
        } catch (error) {
            const message = error.response?.data?.detail || 'Error adding language';
            UI.showToast(message, 'error');
        } finally {
            UI.setButtonLoading(button, false);
        }
    },
    
    /**
     * Handle text file upload
     */
    async handleTextFileUpload(e) {
        e.preventDefault();
        
        const button = DOM.buttons.upload;
        const fileInput = DOM.fileUpload.textInput;
        const file = fileInput.files[0];
        
        if (!file) {
            UI.setStatusMessage(DOM.messages.upload, 'Please select a file first', 'warning');
            return;
        }
        
        if (file.size > CONFIG.FILE_SIZE_LIMIT) {
            UI.setStatusMessage(DOM.messages.upload, 'File size exceeds 10MB limit', 'error');
            return;
        }
        
        UI.setButtonLoading(button, true, 'Uploading...');
        UI.clearStatusMessage(DOM.messages.upload);
        UI.clearStatusMessage(DOM.messages.duplicate);
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await API.files.uploadText(formData);
            UI.setStatusMessage(DOM.messages.upload, response.data.message, 'success');
            
            // Handle skipped items
            if (response.data.skipped && response.data.skipped.length > 0) {
                UI.displayList(DOM.messages.duplicate, response.data.skipped, 'error', 'Skipped values:');
            }
            
            // Reset form
            fileInput.value = '';
            DOM.fileUpload.textDisplay.textContent = 'No file selected';
        } catch (error) {
            const message = error.response?.data?.detail || 'Error uploading file';
            UI.setStatusMessage(DOM.messages.upload, message, 'error');
        } finally {
            UI.setButtonLoading(button, false);
        }
    },
    
    /**
     * Handle Excel file upload
     */
    async handleExcelFileUpload(e) {
        e.preventDefault();
        
        const lang = DOM.selects.languageExcel.value;
        const button = DOM.buttons.uploadExcel;
        const fileInput = DOM.fileUpload.excelInput;
        const file = fileInput.files[0];
        
        if (!lang) {
            UI.setStatusMessage(DOM.messages.excelUpload, 'Please select a language first', 'warning');
            return;
        }
        
        if (!file) {
            UI.setStatusMessage(DOM.messages.excelUpload, 'Please select a file first', 'warning');
            return;
        }
        
        if (file.size > CONFIG.FILE_SIZE_LIMIT) {
            UI.setStatusMessage(DOM.messages.excelUpload, 'File size exceeds 10MB limit', 'error');
            return;
        }
        
        UI.setButtonLoading(button, true, 'Uploading...');
        UI.clearStatusMessage(DOM.messages.excelUpload);
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await API.files.uploadExcel(lang, formData);
            const message = `${response.data.message}. Processed ${response.data.total_valid_rows} of ${response.data.total_excel_rows} rows.`;
            UI.setStatusMessage(DOM.messages.excelUpload, message, 'success');
            
            // Reset form
            fileInput.value = '';
            DOM.fileUpload.excelDisplay.textContent = 'No file selected';
        } catch (error) {
            const message = error.response?.data?.detail || 'Error uploading Excel file';
            UI.setStatusMessage(DOM.messages.excelUpload, message, 'error');
        } finally {
            UI.setButtonLoading(button, false);
        }
    },
    
    /**
     * Handle PO file generation
     */
    async handleGeneratePO() {
        const lang = DOM.selects.language.value;
        const button = DOM.buttons.selectPO;
        
        if (!lang) {
            UI.setStatusMessage(DOM.messages.selectPO, 'Please select a language first', 'warning');
            return;
        }
        
        UI.setButtonLoading(button, true, 'Generating PO...');
        UI.clearStatusMessage(DOM.messages.selectPO);
        
        try {
            const response = await API.files.generatePO(lang);
            UI.setStatusMessage(DOM.messages.selectPO, response.data.message, 'success');
        } catch (error) {
            const message = error.response?.data?.detail || 'Error generating PO file';
            UI.setStatusMessage(DOM.messages.selectPO, message, 'error');
        } finally {
            UI.setButtonLoading(button, false);
        }
    },
    
    /**
     * Handle MO file generation
     */
    async handleGenerateMO() {
        const lang = DOM.selects.language.value;
        const button = DOM.buttons.selectMO;
        
        if (!lang) {
            UI.setStatusMessage(DOM.messages.selectMO, 'Please select a language first', 'warning');
            return;
        }
        
        UI.setButtonLoading(button, true, 'Generating MO...');
        UI.clearStatusMessage(DOM.messages.selectMO);
        UI.clearStatusMessage(DOM.messages.mo);
        
        try {
            const response = await API.files.generateMO(lang);
            UI.setStatusMessage(DOM.messages.selectMO, response.data.message, 'success');
        } catch (error) {
            const message = error.response?.data?.detail || 'Error generating MO file';
            UI.displayErrorList(DOM.messages.mo, message);
        } finally {
            UI.setButtonLoading(button, false);
        }
    },
    
    /**
     * Handle Excel download
     */
    async handleExcelDownload() {
        const button = DOM.buttons.downloadExcel;
        const statusMessage = DOM.messages.downloadStatus;
        
        UI.setButtonLoading(button, true, 'Generating Excel File...');
        UI.clearStatusMessage(statusMessage);
        
        try {
            const response = await fetch(`${CONFIG.API_BASE}/export`);
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            // Extract filename from headers
            const contentDisposition = response.headers.get('content-disposition');
            let filename = 'language_strings.xlsx';
            
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }
            
            // Create download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            UI.setStatusMessage(statusMessage, 'File downloaded successfully!', 'success');
        } catch (error) {
            console.error('Download error:', error);
            UI.setStatusMessage(statusMessage, 'Error downloading file. Please try again.', 'error');
        } finally {
            UI.setButtonLoading(button, false);
            button.innerHTML = '<i class="fas fa-download"></i> Download Excel File';
        }
    },
};

// ===========================
// Connection Monitor
// ===========================
const ConnectionMonitor = {
    /**
     * Start monitoring API connection
     */
    start() {
        this.check();
        AppState.connectionCheckInterval = setInterval(() => {
            this.check();
        }, CONFIG.CONNECTION_CHECK_INTERVAL);
    },
    
    /**
     * Stop monitoring
     */
    stop() {
        if (AppState.connectionCheckInterval) {
            clearInterval(AppState.connectionCheckInterval);
            AppState.connectionCheckInterval = null;
        }
    },
    
    /**
     * Check connection status
     */
    async check() {
        const isConnected = await API.checkConnection();
        UI.updateConnectionStatus(isConnected);
        
        if (!AppState.isConnected && isConnected) {
            // Connection restored
            await LanguageManager.loadLanguages();
            UI.showToast('Connection restored', 'success');
        }
    },
};

// ===========================
// Application Initialization
// ===========================
const App = {
    /**
     * Initialize the application
     */
    async init() {
        try {
            // Initialize components
            this.attachEventListeners();
            FileHandlers.init();
            
            // Load initial data
            await LanguageManager.loadLanguages();
            
            // Start monitoring
            ConnectionMonitor.start();
            
            console.log('✅ Application initialized successfully');
        } catch (error) {
            console.error('❌ Application initialization failed:', error);
            UI.showToast('Application initialization failed', 'error');
        }
    },
    
    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Form submissions
        DOM.forms.language?.addEventListener('submit', (e) => FormHandlers.handleLanguageSubmit(e));
        DOM.forms.upload?.addEventListener('submit', (e) => FormHandlers.handleTextFileUpload(e));
        DOM.forms.excelUpload?.addEventListener('submit', (e) => FormHandlers.handleExcelFileUpload(e));
        
        // Button clicks
        DOM.buttons.selectPO?.addEventListener('click', () => FormHandlers.handleGeneratePO());
        DOM.buttons.selectMO?.addEventListener('click', () => FormHandlers.handleGenerateMO());
        DOM.buttons.downloadExcel?.addEventListener('click', () => FormHandlers.handleExcelDownload());
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            ConnectionMonitor.stop();
        });
    },
};

// ===========================
// Start Application
// ===========================
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});