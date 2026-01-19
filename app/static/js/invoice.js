// Invoice-specific JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    initInvoicePrinting();
    initInvoiceActions();
});

// Initialize invoice printing
function initInvoicePrinting() {
    const printButtons = document.querySelectorAll('.btn-print, [onclick*="print"]');

    printButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            printInvoice();
        });
    });
}

// Print invoice
function printInvoice() {
    // Hide non-printable elements
    const buttons = document.querySelectorAll('.btn');
    const navbars = document.querySelectorAll('.navbar');
    const footers = document.querySelectorAll('.footer');

    // Store original display values
    const originalDisplays = [];

    buttons.forEach(function(el) {
        originalDisplays.push({ el, display: el.style.display });
        el.style.display = 'none';
    });

    navbars.forEach(function(el) {
        originalDisplays.push({ el, display: el.style.display });
        el.style.display = 'none';
    });

    footers.forEach(function(el) {
        originalDisplays.push({ el, display: el.style.display });
        el.style.display = 'none';
    });

    // Print
    window.print();

    // Restore original display values after printing
    setTimeout(function() {
        originalDisplays.forEach(function(item) {
            item.el.style.display = item.display;
        });
    }, 1000);
}

// Initialize invoice actions
function initInvoiceActions() {
    // Download as PDF (if supported)
    const downloadButtons = document.querySelectorAll('.btn-download-pdf');
    downloadButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            downloadInvoiceAsPDF();
        });
    });

    // Email invoice
    const emailButtons = document.querySelectorAll('.btn-email-invoice');
    emailButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            emailInvoice();
        });
    });
}

// Download invoice as PDF
function downloadInvoiceAsPDF() {
    const invoiceElement = document.querySelector('.card-body');
    if (!invoiceElement) {
        showAlert('Invoice element not found', 'danger');
        return;
    }

    // Check if html2pdf is available
    if (typeof html2pdf !== 'undefined') {
        const opt = {
            margin: 1,
            filename: `invoice_${getInvoiceNumber()}.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
        };

        html2pdf().set(opt).from(invoiceElement).save();
    } else {
        // Fallback: print to PDF
        printInvoice();
        showAlert('PDF download not available. Please use your browser\'s print to PDF feature.', 'warning');
    }
}

// Email invoice
function emailInvoice() {
    const invoiceNumber = getInvoiceNumber();
    const subject = `Invoice ${invoiceNumber}`;
    const body = `Please find attached invoice ${invoiceNumber}.\n\nGenerated on: ${new Date().toLocaleString()}`;

    const mailtoLink = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.location.href = mailtoLink;
}

// Get invoice number from page
function getInvoiceNumber() {
    const invoiceTitle = document.querySelector('h1, h4');
    if (invoiceTitle) {
        const match = invoiceTitle.textContent.match(/#(\d+)/);
        if (match) {
            return match[1];
        }
    }
    return 'invoice';
}

// Auto-print functionality
function autoPrintInvoice() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('print') === 'true') {
        setTimeout(function() {
            printInvoice();
        }, 500);
    }
}

// Share invoice
function shareInvoice() {
    if (navigator.share) {
        navigator.share({
            title: `Invoice ${getInvoiceNumber()}`,
            text: 'Check out this invoice',
            url: window.location.href
        });
    } else {
        // Fallback: copy link
        copyToClipboard(window.location.href);
    }
}

// Copy invoice link
function copyInvoiceLink() {
    copyToClipboard(window.location.href);
    showAlert('Invoice link copied to clipboard!', 'success');
}

// Helper functions
function showAlert(message, type = 'info') {
    if (window.GroceryApp && window.GroceryApp.showAlert) {
        window.GroceryApp.showAlert(message, type);
    } else {
        alert(message);
    }
}

function copyToClipboard(text) {
    if (window.GroceryApp && window.GroceryApp.copyToClipboard) {
        window.GroceryApp.copyToClipboard(text);
    } else if (navigator.clipboard) {
        navigator.clipboard.writeText(text);
    }
}

// Initialize auto-print on page load
document.addEventListener('DOMContentLoaded', function() {
    autoPrintInvoice();
});

// Export for global use
window.InvoiceUtils = {
    printInvoice,
    downloadInvoiceAsPDF,
    emailInvoice,
    shareInvoice,
    copyInvoiceLink
};