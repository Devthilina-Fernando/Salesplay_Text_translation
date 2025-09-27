// Configuration
const API_BASE = "http://localhost:8000/api";
const CONNECTION_CHECK_INTERVAL = 30000; // 30 seconds

// DOM Elements
const elements = {
    fileUpload: document.getElementById('file-upload'),
    excelfileUpload: document.getElementById('excel-file-upload'),
    fileNameDisplay: document.getElementById('file-name'),
    excelfileNameDisplay: document.getElementById('excel-file-name'),
    dropZone: document.getElementById('drop-zone'),
    dropZoneexcel: document.getElementById('drop-zone-excel'),
    languageForm: document.getElementById('language-form'),
    uploadForm: document.getElementById('upload-form'),
    exceluploadForm: document.getElementById('upload-excel'),
    languageSelect: document.getElementById('language-select'),
    languageSelectExcel: document.getElementById('language-select-excel'),
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
    elements.exceluploadForm.addEventListener('submit', handleExcelFileUpload);
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
        elements.languageSelectExcel.innerHTML = '<option value="">Loading languages...</option>';
        const response = await axios.get(`${API_BASE}/get_all_languages`);
        const languages = response.data;
        
        elements.languageSelect.innerHTML = languages.length 
            ? '<option value="">Select a language</option>'
            : '<option value="">No languages available</option>';

        elements.languageSelectExcel.innerHTML = languages.length 
            ? '<option value="">Select a language</option>'
            : '<option value="">No languages available</option>';

        languages.forEach(lang => {
            // Create separate option elements for each dropdown
            const option1 = document.createElement('option');
            option1.value = lang;
            option1.textContent = lang;
            elements.languageSelect.appendChild(option1);

            const option2 = document.createElement('option');
            option2.value = lang;
            option2.textContent = lang;
            elements.languageSelectExcel.appendChild(option2);
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
// function populateDemoLanguages() {
//     const languages = ['en_US', 'fr_FR', 'de_DE', 'es_ES', 'ja_JP'];
//     const grid = document.getElementById('language-grid');
    
//     languages.forEach(lang => {
//         const card = document.createElement('div');
//         card.className = 'language-card';
//         card.dataset.lang = lang;
//         card.innerHTML = `
//             <i class="fas fa-flag"></i>
//             <h3>${lang}</h3>
//             <p>${lang.split('_')[0]}</p>
//         `;
//         grid.appendChild(card);
//     });
// }



/////////////////////////////////////////////////////////

document.addEventListener('DOMContentLoaded', function() {
    const downloadBtn = document.getElementById('download-excel-btn');
    const statusMessage = document.getElementById('download-status-message');
    
    downloadBtn.addEventListener('click', function() {
        // Show loading state
        downloadBtn.disabled = true;
        downloadBtn.innerHTML = '<span class="loading-spinner"></span> Generating Excel File...';
        statusMessage.style.display = 'none';
        
        // API endpoint (note: fixed the typo from "loaclhost" to "localhost")
        const apiUrl = 'http://127.0.0.1:8000/api/export';
        
        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                
                // Extract filename from content-disposition header
                const contentDisposition = response.headers.get('content-disposition');
                let filename = 'language_strings.xlsx';
                
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                    if (filenameMatch) {
                        filename = filenameMatch[1];
                    }
                }
                
                return response.blob().then(blob => {
                    return { blob, filename };
                });
            })
            .then(({ blob, filename }) => {
                // Create a download link and trigger the download
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                
                // Clean up
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                // Show success message
                statusMessage.textContent = 'File downloaded successfully!';
                statusMessage.classList.remove('download-error');
                statusMessage.style.display = 'block';
            })
            .catch(error => {
                console.error('Error downloading file:', error);
                statusMessage.textContent = 'Error downloading file. Please try again.';
                statusMessage.classList.add('download-error');
                statusMessage.style.display = 'block';
            })
            .finally(() => {
                // Reset button state
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = '<i class="fas fa-download"></i> Download Excel File';
            });
    });
});

////// excel file upload handling //////




// // excel Upload function
// async function handleExcelUpload(lang, file) {


//     e.preventDefault();
    
//     const btn = document.getElementById('add-language-btn');
//     const originalText = btn.innerHTML;
//     btn.innerHTML = '<div class="loading"></div> Processing...';
//     btn.disabled = true;
    
//     const language = {
//         language: document.getElementById('name').value.trim(),
//         language_code: document.getElementById('lang-string').value.trim(),
//         language_name: document.getElementById('display-name').value.trim()
//     };




    

//     // const lang_excel = elements.languageSelect2.value;
//     // const btn = document.getElementById('excel-upload-btn');
    
//     if (!lang_excel) {
//         setStatusMessage(elements.selectMoMessage, 'Please select a language first', 'warning');
//         return;
//     }

//     const originalTextExcel = btn.innerHTML;
//     btn.innerHTML = '<div class="loading"></div> Generating...';
//     btn.disabled = true;
//     clearStatusMessage(elements.selectMoMessage);
//     clearStatusMessage(elements.moMessage);

//     const excelfile = elements.excelfileUpload.files[0];
//     const excelformData = new FormData();
//     excelformData.append('file', file);

//     try {
//         // In a real application, you would use the actual API endpoint
//         const response_excel = await fetch(`${API_BASE}/excel-import/${lang}`, {
//             method: 'POST',
//             body: excelformData
//         });
        
//         const data = await response_excel.json();
        
//         // Simulate API response for demonstration
//         await new Promise(resolve => setTimeout(resolve, 1500));
        
//         // Simulated response based on the example provided
//         // const data = {
//         //     message: `Successfully updated 7565 records with ${lang}=1`,
//         //     total_valid_rows: 7565,
//         //     total_excel_rows: 7566
//         // };
        
//         setStatusMessage(`${data.message}. Processed ${data.total_valid_rows} of ${data.total_excel_rows} rows.`, 'success');
//     } catch (error) {
//         let msg = error.response?.data?.detail || 'Error uploading Excel file';
        
//         if (msg.includes('\n')) {
//             // Create bullet list for multi-line errors
//             let html = '<p>Upload failed:</p><ul class="error-list">';
            
//             msg.split('\n')
//                 .filter(line => line.trim() !== '')
//                 .forEach(line => {
//                     html += `<li>${line}</li>`;
//                 });
            
//             html += '</ul>';
//             uploadMessage.innerHTML = html;
//         } else {
//             setStatusMessage(msg, 'error');
//         }
//     } finally {
//         uploadBtn.innerHTML = originalTextExcel;
//         uploadBtn.disabled = false;
//     }
// }


async function handleExcelFileUpload(e) {
    e.preventDefault();
    const excel_lang = elements.languageSelectExcel.value;
    const btn = document.getElementById('excel-upload-btn');
    
    if (!elements.excelfileUpload.files.length) {
        setStatusMessage(elements.uploadMessage, 'Please select a file first', 'warning');
        return;
    }

    const originalText = btn.innerHTML;
    btn.innerHTML = '<div class="loading"></div> Uploading...';
    btn.disabled = true;
    
    const excelfile = elements.excelfileUpload.files[0];
    const excelformData = new FormData();
    excelformData.append('file', excelfile);

    try {
        const res = await axios.post(`${API_BASE}/excel-import/${excel_lang}`, excelformData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        setStatusMessage(elements.uploadMessage, res.data.message, 'success');
        elements.excelfileUpload.value = '';
        elements.excelfileNameDisplay.textContent = 'No file selected';

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
