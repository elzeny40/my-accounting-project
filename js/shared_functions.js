/**
 * Shared JavaScript functions for Kayan application
 */

// Get CSRF token from cookies for AJAX requests
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function formatNumber(number, decimals = 2) {
    return Number(number).toFixed(decimals);
}

function formatDate(date) {
    return new Date(date).toISOString().split('T')[0];
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('ar-EG', {
        style: 'currency',
        currency: 'EGP'
    }).format(amount);
}

function showLoadingSpinner(message = 'جاري التحميل...') {
    return Swal.fire({
        title: message,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
}

function handleAjaxError(error, customMessage = null) {
    console.error('Error:', error);
    Swal.fire({
        title: 'خطأ',
        text: customMessage || 'حدث خطأ أثناء تنفيذ العملية',
        icon: 'error',
        confirmButtonText: 'حسناً'
    });
}

function confirmDelete(message = 'هل أنت متأكد من الحذف؟') {
    return Swal.fire({
        title: 'تأكيد الحذف',
        text: message,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'نعم، احذف',
        cancelButtonText: 'إلغاء'
    });
}

function showSuccess(message = 'تم تنفيذ العملية بنجاح') {
    return Swal.fire({
        title: 'تم',
        text: message,
        icon: 'success',
        confirmButtonText: 'حسناً'
    });
}

// Form utilities
function clearForm(formElement) {
    formElement.reset();
    // Clear Select2 dropdowns if they exist
    $(formElement).find('select').each(function() {
        if ($(this).hasClass('select2-hidden-accessible')) {
            $(this).val(null).trigger('change');
        }
    });
}

function serializeForm(formElement) {
    const formData = new FormData(formElement);
    const data = {};
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    return data;
}

// Data table utilities
function initializeDataTable(tableId, options = {}) {
    const defaultOptions = {
        language: {
            url: '//cdn.datatables.net/plug-ins/1.10.24/i18n/Arabic.json'
        },
        order: [[0, 'desc']],
        pageLength: 25,
        responsive: true
    };
    
    return $(tableId).DataTable({ ...defaultOptions, ...options });
}

// Export utilities
function exportTableToExcel(tableId, fileName) {
    const table = document.getElementById(tableId);
    const wb = XLSX.utils.table_to_book(table, { sheet: "Sheet 1" });
    XLSX.writeFile(wb, fileName);
}

// Print utilities
function printElement(elementId) {
    const element = document.getElementById(elementId);
    const originalContents = document.body.innerHTML;
    
    document.body.innerHTML = element.innerHTML;
    window.print();
    document.body.innerHTML = originalContents;
    
    // Reinitialize any JS components that were destroyed
    location.reload();
}

// CRUD operation handler factory
function handleCRUD(baseUrl) {
    return {
        view: function(id) {
            window.location.href = `${baseUrl}/${id}/view/`;
        },
        edit: function(id) {
            window.location.href = `${baseUrl}/${id}/edit/`;
        },
        delete: function(id) {
            if (confirm('هل أنت متأكد من الحذف؟')) {
                fetch(`${baseUrl}/${id}/delete/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                }).then(response => {
                    if (response.ok) {
                        location.reload();
                    }
                });
            }
        }
    };
}