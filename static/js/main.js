/**
 * C-Recenzione - Main JavaScript file
 * Manages client-side interactions for the review request system
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize tooltips and popovers
    initializeBootstrapComponents();
    
    // Setup event listeners
    setupEventListeners();
    
    // Initialize company and template selectors on the dashboard
    initializeDashboardSelectors();
});

/**
 * Initialize Bootstrap components like tooltips and popovers
 */
function initializeBootstrapComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Set up event listeners for various interactive elements
 */
function setupEventListeners() {
    // Company form validation
    const companyForm = document.getElementById('companyForm');
    if (companyForm) {
        companyForm.addEventListener('submit', validateCompanyForm);
    }
    
    // Template form validation
    const templateForm = document.getElementById('templateForm');
    if (templateForm) {
        templateForm.addEventListener('submit', validateTemplateForm);
    }
    
    // Generate review request button
    const generateBtn = document.getElementById('generateRequestBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateReviewRequest);
    }
    
    // Send review request button
    const sendBtn = document.getElementById('sendRequestBtn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendReviewRequest);
    }
    
    // Company deletion confirmation
    const deleteCompanyBtns = document.querySelectorAll('.delete-company-btn');
    deleteCompanyBtns.forEach(btn => {
        btn.addEventListener('click', confirmDeleteCompany);
    });
    
    // Template deletion confirmation
    const deleteTemplateBtns = document.querySelectorAll('.delete-template-btn');
    deleteTemplateBtns.forEach(btn => {
        btn.addEventListener('click', confirmDeleteTemplate);
    });
    
    // Category filter for companies
    const categoryFilter = document.getElementById('categoryFilter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', filterCompaniesByCategory);
    }
}

/**
 * Initialize dashboard selectors for companies and templates
 */
function initializeDashboardSelectors() {
    const companySelect = document.getElementById('companySelect');
    const templateSelect = document.getElementById('templateSelect');
    const categoryFilterDashboard = document.getElementById('categoryFilterDashboard');
    
    if (companySelect && templateSelect && categoryFilterDashboard) {
        // Filter companies and templates when category changes
        categoryFilterDashboard.addEventListener('change', function() {
            const selectedCategory = this.value;
            
            // Filter companies
            const companyOptions = companySelect.querySelectorAll('option:not(:first-child)');
            companyOptions.forEach(option => {
                const companyCategory = option.getAttribute('data-category');
                if (selectedCategory === '' || companyCategory === selectedCategory) {
                    option.style.display = '';
                } else {
                    option.style.display = 'none';
                }
            });
            
            // Filter templates
            const templateOptions = templateSelect.querySelectorAll('option:not(:first-child)');
            templateOptions.forEach(option => {
                const templateCategory = option.getAttribute('data-category');
                if (selectedCategory === '' || templateCategory === 'general' || templateCategory === selectedCategory) {
                    option.style.display = '';
                } else {
                    option.style.display = 'none';
                }
            });
            
            // Reset selections
            companySelect.selectedIndex = 0;
            templateSelect.selectedIndex = 0;
            
            // Clear message preview
            document.getElementById('messagePreview').innerHTML = '';
            document.getElementById('previewContainer').style.display = 'none';
            
            // Disable send button
            document.getElementById('sendRequestBtn').disabled = true;
        });
    }
}

/**
 * Validate company form before submission
 */
function validateCompanyForm(event) {
    const nameInput = document.getElementById('companyName');
    const emailInput = document.getElementById('companyEmail');
    const categoryInput = document.getElementById('companyCategory');
    
    let isValid = true;
    
    // Validate name
    if (!nameInput.value.trim()) {
        nameInput.classList.add('is-invalid');
        isValid = false;
    } else {
        nameInput.classList.remove('is-invalid');
    }
    
    // Validate email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailInput.value.trim() || !emailRegex.test(emailInput.value.trim())) {
        emailInput.classList.add('is-invalid');
        isValid = false;
    } else {
        emailInput.classList.remove('is-invalid');
    }
    
    // Validate category
    if (!categoryInput.value) {
        categoryInput.classList.add('is-invalid');
        isValid = false;
    } else {
        categoryInput.classList.remove('is-invalid');
    }
    
    if (!isValid) {
        event.preventDefault();
    }
}

/**
 * Validate template form before submission
 */
function validateTemplateForm(event) {
    const nameInput = document.getElementById('templateName');
    const categoryInput = document.getElementById('templateCategory');
    const contentInput = document.getElementById('templateContent');
    
    let isValid = true;
    
    // Validate name
    if (!nameInput.value.trim()) {
        nameInput.classList.add('is-invalid');
        isValid = false;
    } else {
        nameInput.classList.remove('is-invalid');
    }
    
    // Validate category
    if (!categoryInput.value) {
        categoryInput.classList.add('is-invalid');
        isValid = false;
    } else {
        categoryInput.classList.remove('is-invalid');
    }
    
    // Validate content
    if (!contentInput.value.trim()) {
        contentInput.classList.add('is-invalid');
        isValid = false;
    } else {
        contentInput.classList.remove('is-invalid');
    }
    
    if (!isValid) {
        event.preventDefault();
    }
}

/**
 * Generate a review request using the AI service
 */
function generateReviewRequest() {
    const companySelect = document.getElementById('companySelect');
    const templateSelect = document.getElementById('templateSelect');
    const messagePreview = document.getElementById('messagePreview');
    const previewContainer = document.getElementById('previewContainer');
    const generateBtn = document.getElementById('generateRequestBtn');
    const sendBtn = document.getElementById('sendRequestBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    
    // Validate selections
    if (companySelect.value === '' || templateSelect.value === '') {
        showAlert('Seleziona un\'azienda e un template per generare la richiesta.', 'danger');
        return;
    }
    
    // Show loading and disable button
    generateBtn.disabled = true;
    loadingIndicator.style.display = 'inline-block';
    messagePreview.innerHTML = '<div class="text-center text-muted">Generazione in corso...</div>';
    previewContainer.style.display = 'block';
    
    // Call the API to generate the request
    fetch('/generate_request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            company_id: companySelect.value,
            template_id: templateSelect.value
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Errore nella richiesta al server');
        }
        return response.json();
    })
    .then(data => {
        // Display the generated message
        if (data.message) {
            messagePreview.innerHTML = formatMessagePreview(data.message);
            // Store company info for sending
            messagePreview.dataset.companyId = companySelect.value;
            messagePreview.dataset.companyName = data.company.name;
            messagePreview.dataset.companyEmail = data.company.email;
            
            // Enable send button
            sendBtn.disabled = false;
        } else {
            messagePreview.innerHTML = '<div class="alert alert-warning">Impossibile generare la richiesta. Riprova più tardi.</div>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        messagePreview.innerHTML = `<div class="alert alert-danger">Errore: ${error.message}</div>`;
    })
    .finally(() => {
        // Hide loading and enable button
        generateBtn.disabled = false;
        loadingIndicator.style.display = 'none';
    });
}

/**
 * Format message preview with proper styling
 */
function formatMessagePreview(message) {
    // Replace newlines with <br> tags
    return message.replace(/\n/g, '<br>');
}

/**
 * Send the generated review request to the company
 */
function sendReviewRequest() {
    const messagePreview = document.getElementById('messagePreview');
    const sendBtn = document.getElementById('sendRequestBtn');
    const sendLoadingIndicator = document.getElementById('sendLoadingIndicator');
    
    // Get data from the preview
    const companyId = messagePreview.dataset.companyId;
    const companyEmail = messagePreview.dataset.companyEmail;
    const message = messagePreview.innerHTML.replace(/<br>/g, '\n');
    
    if (!companyId || !message) {
        showAlert('Dati mancanti per l\'invio della richiesta.', 'danger');
        return;
    }
    
    // Confirm before sending
    if (!confirm(`Sei sicuro di voler inviare questa richiesta a ${companyEmail}?`)) {
        return;
    }
    
    // Show loading and disable button
    sendBtn.disabled = true;
    sendLoadingIndicator.style.display = 'inline-block';
    
    // Call the API to send the request
    fetch('/send_request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            company_id: companyId,
            message: message,
            subject: 'Richiesta di recensione prodotto - C-Recenzione'
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Errore nell\'invio della richiesta');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showAlert('Richiesta inviata con successo!', 'success');
            
            // Reset form
            document.getElementById('companySelect').selectedIndex = 0;
            document.getElementById('templateSelect').selectedIndex = 0;
            messagePreview.innerHTML = '';
            document.getElementById('previewContainer').style.display = 'none';
            sendBtn.disabled = true;
        } else {
            showAlert(`Errore: ${data.error || 'Si è verificato un errore durante l\'invio.'}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert(`Errore: ${error.message}`, 'danger');
    })
    .finally(() => {
        // Hide loading indicator
        sendLoadingIndicator.style.display = 'none';
        sendBtn.disabled = false;
    });
}

/**
 * Confirm company deletion
 */
function confirmDeleteCompany(event) {
    const companyId = event.target.dataset.companyId;
    const companyName = event.target.dataset.companyName;
    
    if (confirm(`Sei sicuro di voler eliminare l'azienda "${companyName}"? Questa operazione non può essere annullata.`)) {
        // Submit the form
        const form = document.getElementById(`deleteCompanyForm-${companyId}`);
        if (form) {
            form.submit();
        }
    }
}

/**
 * Confirm template deletion
 */
function confirmDeleteTemplate(event) {
    const templateId = event.target.dataset.templateId;
    const templateName = event.target.dataset.templateName;
    
    if (confirm(`Sei sicuro di voler eliminare il template "${templateName}"? Questa operazione non può essere annullata.`)) {
        // Submit the form
        const form = document.getElementById(`deleteTemplateForm-${templateId}`);
        if (form) {
            form.submit();
        }
    }
}

/**
 * Filter companies by category
 */
function filterCompaniesByCategory() {
    const selectedCategory = this.value;
    const companyRows = document.querySelectorAll('.company-row');
    
    companyRows.forEach(row => {
        const rowCategory = row.dataset.category;
        if (selectedCategory === '' || rowCategory === selectedCategory) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    // Create alert container if it doesn't exist
    let alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alertContainer';
        alertContainer.style.position = 'fixed';
        alertContainer.style.top = '20px';
        alertContainer.style.right = '20px';
        alertContainer.style.zIndex = '9999';
        document.body.appendChild(alertContainer);
    }
    
    // Create alert
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    alertContainer.appendChild(alertElement);
    
    // Initialize dismissible functionality
    new bootstrap.Alert(alertElement);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = bootstrap.Alert.getInstance(alertElement);
        if (bsAlert) {
            bsAlert.close();
        }
    }, 5000);
}
