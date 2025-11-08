/**
 * Scanner Server - Main JavaScript
 */

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Scanner Server initialized');

    // Load printers if on home page
    if (document.getElementById('printer')) {
        loadPrinters();
    }

    // Setup print form handler
    const printForm = document.getElementById('printForm');
    if (printForm) {
        printForm.addEventListener('submit', handlePrintSubmit);
    }

    // Load recent scans if element exists
    if (document.getElementById('recentScans')) {
        loadRecentScans();
    }
});

/**
 * Load available printers
 */
async function loadPrinters() {
    const printerSelect = document.getElementById('printer');
    if (!printerSelect) return;

    try {
        const response = await fetch('/api/printer/list', {
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load printers');
        }

        const data = await response.json();

        if (data.success && data.printers && data.printers.length > 0) {
            printerSelect.innerHTML = '<option value="">Select a printer...</option>';

            data.printers.forEach(printer => {
                const option = document.createElement('option');
                option.value = printer.name || printer;
                option.textContent = printer.name || printer;
                printerSelect.appendChild(option);
            });
        } else {
            printerSelect.innerHTML = '<option value="">No printers available</option>';
        }
    } catch (error) {
        console.error('Error loading printers:', error);
        printerSelect.innerHTML = '<option value="">Error loading printers</option>';
        showAlert('error', 'Failed to load printers. Please check your printer configuration.');
    }
}

/**
 * Handle print form submission
 */
async function handlePrintSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const fileInput = form.querySelector('#file');
    const printerSelect = form.querySelector('#printer');
    const submitButton = form.querySelector('button[type="submit"]');

    // Validate inputs
    if (!fileInput.files.length) {
        showAlert('error', 'Please select a file to print');
        return;
    }

    if (!printerSelect.value) {
        showAlert('error', 'Please select a printer');
        return;
    }

    // Disable submit button
    submitButton.disabled = true;
    submitButton.textContent = 'Printing...';

    try {
        const formData = new FormData(form);

        const response = await fetch('/api/printer/print', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showAlert('success', 'Document sent to printer successfully!');
            form.reset();
        } else {
            showAlert('error', `Print failed: ${data.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error printing:', error);
        showAlert('error', 'Failed to print document. Please try again.');
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'Print Document';
    }
}

/**
 * Load recent scans (placeholder implementation)
 */
async function loadRecentScans() {
    const recentScansDiv = document.getElementById('recentScans');
    if (!recentScansDiv) return;

    // TODO: Implement actual API endpoint for recent scans
    // For now, show a placeholder message
    setTimeout(() => {
        recentScansDiv.innerHTML = '<p class="text-center" style="color: #7f8c8d;">No recent scans to display</p>';
    }, 500);
}

/**
 * Show alert message
 */
function showAlert(type, message) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());

    // Create new alert
    const alert = document.createElement('div');
    alert.className = `alert ${type}`;
    alert.textContent = message;

    // Insert at top of main content
    const main = document.querySelector('main.container');
    if (main) {
        main.insertBefore(alert, main.firstChild);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
}

/**
 * Make API request with error handling
 */
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Accept': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
