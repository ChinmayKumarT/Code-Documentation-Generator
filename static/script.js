document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const fileInput = document.getElementById('file-input');
    const uploadButton = document.getElementById('upload-button');
    const generateFromCodeBtn = document.getElementById('generate-from-code');
    const codeInput = document.getElementById('code-input');
    const copyButton = document.getElementById('copy-code');
    const languageSelect = document.getElementById('language-select');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    const resultsSection = document.getElementById('results-section');
    const jsonLink = document.getElementById('json-link');
    const pdfLink = document.getElementById('pdf-link');
    const loadingSpinner = document.getElementById('loading-spinner');
    const errorMessage = document.getElementById('error-message');

    // Tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            // Update active tab button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Show corresponding tab content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === tabId) {
                    content.classList.add('active');
                }
            });
            
            // Hide results when switching tabs
            hideResults();
        });
    });

    // File upload handling
    fileInput.addEventListener('change', updateFileName);
    
    // Handle file drop
    const dropArea = document.querySelector('.file-upload-area');
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropArea.style.borderColor = 'var(--primary)';
        dropArea.style.background = 'rgba(108, 99, 255, 0.1)';
    }
    
    function unhighlight() {
        dropArea.style.borderColor = 'var(--gray)';
        dropArea.style.background = 'rgba(30, 41, 59, 0.5)';
    }
    
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length) {
            fileInput.files = files;
            updateFileName();
        }
    }
    
    function updateFileName() {
        const fileNameSpan = document.getElementById('file-name');
        if (fileInput.files.length > 0) {
            fileNameSpan.textContent = fileInput.files[0].name;
            fileNameSpan.style.display = 'block';
        } else {
            fileNameSpan.textContent = '';
            fileNameSpan.style.display = 'none';
        }
    }

    // Upload file button click
    uploadButton.addEventListener('click', handleFileUpload);
    
    // Generate from code button click
    generateFromCodeBtn.addEventListener('click', handleCodePaste);
    
    // Copy code button
    copyButton.addEventListener('click', copyToClipboard);

    async function handleFileUpload() {
        if (fileInput.files.length === 0) {
            showError('Please select a file first.');
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        await sendRequest('/upload', formData);
    }
    
    async function handleCodePaste() {
        const code = codeInput.value.trim();
        const language = languageSelect.value;
        
        if (!code) {
            showError('Please paste your code first.');
            return;
        }
        
        const formData = new FormData();
        formData.append('code', code);
        formData.append('language', language);
        
        await sendRequest('/paste', formData);
    }
    
    async function sendRequest(url, formData) {
        try {
            showLoading();
            hideError();
            hideResults();

            console.log('Sending request to:', url);
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || 'Failed to generate report');
            }

            const data = await response.json();
            console.log('Server response:', data);

            if (data.files && data.files.json) {
                // Show the results with the first available file
                const fileType = Object.keys(data.files)[0];
                const fileInfo = data.files[fileType];
                showResults(fileInfo.url, fileInfo.filename);
            } else {
                throw new Error('Invalid response format from server');
            }
        } catch (error) {
            console.error('Error:', error);
            showError(error.message || 'An error occurred while generating the report');
        } finally {
            hideLoading();
        }
    }
    
    function copyToClipboard() {
        codeInput.select();
        document.execCommand('copy');
        
        // Show copied feedback
        const originalText = copyButton.innerHTML;
        copyButton.innerHTML = '<i class="fas fa-check"></i>';
        copyButton.title = 'Copied!';
        
        setTimeout(() => {
            copyButton.innerHTML = originalText;
            copyButton.title = 'Copy to clipboard';
        }, 2000);
    }

    function showLoading() {
        console.log('Showing loading overlay');
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.classList.add('visible');
            // Force reflow to enable the transition
            void loadingOverlay.offsetHeight;
        }
        
        // Disable form elements while loading
        const formElements = document.querySelectorAll('button, input, textarea, select');
        formElements.forEach(el => {
            el.disabled = true;
        });
    }

    function hideLoading() {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.classList.remove('visible');
        }
        
        // Re-enable form elements
        const formElements = document.querySelectorAll('button, input, textarea, select');
        formElements.forEach(el => {
            el.disabled = false;
        });
        
        console.log('Loading overlay hidden');
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        errorMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Auto-hide error after 5 seconds
        setTimeout(hideError, 5000);
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }

    function showResults(jsonUrl, filename) {
        console.log('showResults called with:', { jsonUrl, filename });
        
        const resultsSection = document.getElementById('results-section');
        if (!resultsSection) {
            console.error('Results section not found in the DOM');
            return;
        }
        
        // Hide any error messages
        hideError();
        
        // Create the results HTML with the original styling
        resultsSection.innerHTML = `
            <h2><i class="fas fa-file-alt"></i> Generated Reports</h2>
            <div class="report-cards">
                <a href="${jsonUrl}" class="report-card" target="_blank">
                    <i class="fas fa-file-code"></i>
                    <span>JSON Report</span>
                </a>
                <a href="${jsonUrl.replace('_report.json', '_report.pdf')}" class="report-card" target="_blank">
                    <i class="fas fa-file-pdf"></i>
                    <span>PDF Report</span>
                </a>
                <a href="${jsonUrl.replace('_report.json', '_report.md')}" class="report-card" target="_blank">
                    <i class="fas fa-file-alt"></i>
                    <span>Markdown Report</span>
                </a>
            </div>
        `;
        
        // Show the results section with animation
        resultsSection.style.display = 'block';
        // Force reflow to enable the transition
        void resultsSection.offsetHeight;
        resultsSection.classList.add('visible');
        
        // Scroll to the results section
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    }

    function hideResults() {
        resultsSection.classList.remove('visible');
        setTimeout(() => {
            resultsSection.style.display = 'none';
        }, 300);
    }
    
    // Initialize
    updateFileName();
});
