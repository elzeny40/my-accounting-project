/**
 * Operations handling for vehicle movements
 */

// Logger utility for consistent debugging
const logger = {
    debug: (msg, data) => console.log(`[DEBUG] ${msg}`, data || ''),
    error: (msg, error) => console.error(`[ERROR] ${msg}`, error || '')
};

// Utility functions
const utils = {
    getCookie(name) {
        const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        return match ? decodeURIComponent(match[2]) : null;
    },

    cleanupModal(modalId) {
        const modalElement = document.getElementById(modalId);
        if (!modalElement) return;
        
        const modalInstance = bootstrap.Modal.getInstance(modalElement);
        if (modalInstance) {
            modalInstance.hide();
            modalInstance.dispose();
        }
        modalElement.remove();
        logger.debug('Modal cleaned up');
    },

    // Add initialization for select elements
    initializeSelect(elementId, options = {}) {
        const element = $(`#${elementId}`);
        if (element.length) {
            element.select2({
                theme: 'bootstrap-5',
                width: '100%',
                placeholder: options.placeholder || 'اختر...',
                allowClear: options.allowClear !== false,
                ...options
            });
        }
    }
};

// Operations module is now consolidated in vehicle_movement.js
// This event listener is kept for backward compatibility
document.addEventListener('DOMContentLoaded', function() {
    // All operations functionality is now handled in vehicle_movement.js
});

// This function is now handled in vehicle_movement.js
function showOperationsList(type) {
    // Redirect to the implementation in vehicle_movement.js
    logger.debug('Redirecting to vehicle_movement.js implementation for operations list:', { type });
    
    if (typeof window.vehicleMovementShowOperationsList === 'function') {
        window.vehicleMovementShowOperationsList(type);
    } else {
        // Fallback to direct implementation if the function is not available
        const operationTypeSelect = document.getElementById('id_operation_type');
        if (operationTypeSelect) {
            operationTypeSelect.value = type;
            operationTypeSelect.dispatchEvent(new Event('change'));
            
            const showOperationsBtn = document.getElementById('showOperationsBtn');
            if (showOperationsBtn) {
                showOperationsBtn.click();
            }
        } else {
            logger.error('Operation type select not found');
            Swal.fire({
                title: 'خطأ',
                text: 'حدث خطأ أثناء تحميل العمليات',
                icon: 'error'
            });
        }
    }
}

// This function is now handled in vehicle_movement.js
function selectOperation(operationId, type) {
    if (!operationId || !type) {
        logger.error('Missing parameters:', { operationId, type });
        return;
    }

    logger.debug('Redirecting to vehicle_movement.js implementation for operation:', { id: operationId, type });
    
    // Use the implementation in vehicle_movement.js
    // First, make sure the operation type is selected
    const operationTypeSelect = document.getElementById('id_operation_type');
    if (operationTypeSelect) {
        operationTypeSelect.value = type;
        operationTypeSelect.dispatchEvent(new Event('change'));
        
        // Then call the vehicle_movement.js implementation
        if (typeof window.vehicleMovementSelectOperation === 'function') {
            window.vehicleMovementSelectOperation(operationId, type);
        } else {
            // Fallback to direct implementation if the function is not available
            const url = `/accounts/api/operations/${type}/${operationId}/`;
            
            // Show loading indicator
            const loadingSwal = Swal.fire({
                title: 'جاري التحميل...',
                text: 'يرجى الانتظار',
                allowOutsideClick: false,
                showConfirmButton: false,
                willOpen: () => {
                    Swal.showLoading();
                }
            });
            
            fetch(url)
                .then(response => {
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                })
                .then(data => {
                    // Update form fields using the vehicle_movement.js function if available
                    if (typeof fillFormFields === 'function') {
                        fillFormFields(data);
                    } else {
                        updateFormFields(data);
                    }
                    
                    // Close loading indicator and show success
                    loadingSwal.close();
                    Swal.fire({
                        title: 'تم',
                        text: 'تم اختيار العملية بنجاح',
                        icon: 'success',
                        timer: 1500,
                        showConfirmButton: false
                    });
                })
                .catch(error => {
                    logger.error('Error selecting operation:', error);
                    loadingSwal.close();
                    Swal.fire({
                        title: 'خطأ',
                        text: 'حدث خطأ أثناء جلب بيانات العملية',
                        icon: 'error',
                        confirmButtonText: 'حسناً'
                    });
                });
        }
    }
}

function updateFormFields(data) {
    logger.debug('Updating form fields with data:', data);
    
    const fields = {
        'id_operation_id': data.id,
        'id_client': data.client,
        'id_oil_type': data.oil_type,
        'id_driver': data.driver,
        'id_quantity': data.quantity,
        'id_loading_location': data.loading_location || '',
        'id_unloading_location': data.unloading_location || '',
        'id_vehicle_number': data.vehicle_number || '',
        'id_driver_freight': data.driver_freight || '',
        'id_client_freight': data.client_freight || ''
    };

    Object.entries(fields).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (!element) {
            logger.debug(`Field not found: ${id}`);
            return;
        }

        try {
            if (element.tagName === 'SELECT') {
                const select2Element = $(`#${id}`);
                if (select2Element.data('select2')) {
                    if (value) {
                        const optionExists = select2Element.find(`option[value='${value}']`).length > 0;
                        if (!optionExists && data[`${id.split('_')[1]}_name`]) {
                            const newOption = new Option(
                                data[`${id.split('_')[1]}_name`],
                                value,
                                true,
                                true
                            );
                            select2Element.append(newOption);
                        }
                        select2Element.val(value).trigger('change');
                    } else {
                        select2Element.val(null).trigger('change');
                    }
                } else {
                    element.value = value || '';
                }
            } else {
                element.value = value || '';
            }
        } catch (error) {
            logger.error(`Error updating field ${id}:`, error);
        }
    });

    // Update dependent fields
    const driverSelect = $('#id_driver');
    if (driverSelect.length && data.driver) {
        driverSelect.trigger('change');
        logger.debug('Triggered driver change event');
    }
}

// Operations handling functionality
document.addEventListener('DOMContentLoaded', function() {
    const movementTypeSelect = document.getElementById('id_movement_type');
    const operationTypeSelect = document.getElementById('id_operation_type');
    const operationFields = document.getElementById('operation-fields');
    
    function updateOperationTypeOptions(isInternal) {
        if (!operationTypeSelect) return;
        
        if (isInternal) {
            $(operationTypeSelect).html(`
                <option value="">اختر نوع العملية</option>
                <option value="sale">مبيعات</option>
                <option value="purchase">مشتريات</option>
            `).val('').trigger('change');
            
            // استدعاء وظيفة تحديث حالة زر عرض العمليات من ملف vehicle_movement.js
            setTimeout(() => {
                if (typeof window.updateShowOperationsButton === 'function') {
                    window.updateShowOperationsButton();
                }
            }, 300); // Increased delay to ensure the select2 has initialized properly
        } else {
            $(operationTypeSelect).val('').trigger('change');
        }
    }
    
    if (movementTypeSelect) {
        movementTypeSelect.addEventListener('change', function() {
            const isInternal = this.value === 'internal';
            
            if (operationFields) {
                operationFields.style.display = isInternal ? 'block' : 'none';
            }
            
            if (operationTypeSelect) {
                operationTypeSelect.disabled = !isInternal;
                updateOperationTypeOptions(isInternal);
            }
        });
        
        // Add change event listener to operation type select
        if (operationTypeSelect) {
            operationTypeSelect.addEventListener('change', function() {
                // تحديث حالة زر عرض العمليات عند تغيير نوع العملية
                if (typeof window.updateShowOperationsButton === 'function') {
                    window.updateShowOperationsButton();
                }
            });
        }

        // Set initial state
        movementTypeSelect.dispatchEvent(new Event('change'));
    }
});

class OperationsHandler {
    constructor() {
        this.table = null;
        this.filters = new Map();
        this.csrfToken = utils.getCookie('csrftoken');
    }

    init() {
        this.initDataTable();
        this.setupFilters();
        this.bindEvents();
        logger.debug('OperationsHandler initialized');
    }

    initDataTable() {
        this.table = $('#operationsTable').DataTable({
            language: { url: '//cdn.datatables.net/plug-ins/1.10.24/i18n/Arabic.json' },
            order: [[1, 'desc']],
            pageLength: 10,
            dom: 'rtip',
            columnDefs: [{ targets: -1, orderable: false }]
        });
    }

    setupFilters() {
        const filterData = {
            oilType: { selector: '#oilTypeFilter', columnIndex: 3 },
            location: { selector: '#locationFilter', columnIndices: [5, 6] }
        };

        for (const [key, config] of Object.entries(filterData)) {
            const values = new Set();
            this.table.rows().every(row => {
                const data = row.data();
                if (Array.isArray(config.columnIndices)) {
                    config.columnIndices.forEach(index => {
                        if (data[index]) values.add(data[index]);
                    });
                } else if (data[config.columnIndex]) {
                    values.add(data[config.columnIndex]);
                }
            });

            const filter = $(config.selector);
            [...values].sort().forEach(value => {
                filter.append($('<option>').val(value).text(value));
            });

            this.filters.set(key, { element: filter, config });
        }
    }

    bindEvents() {
        $('#operationSearch').on('keyup', e => {
            this.table.search(e.target.value).draw();
        });

        this.filters.forEach(({element}) => {
            element.on('change', () => this.applyFilters());
        });

        $(document).on('click', '.select-operation', e => this.handleOperationSelect(e));
    }

    applyFilters() {
        const filterValues = new Map(
            Array.from(this.filters.entries()).map(([key, {element}]) => [key, element.val()])
        );

        $.fn.dataTable.ext.search.push((settings, data) => {
            const oilTypeMatch = !filterValues.get('oilType') || data[3] === filterValues.get('oilType');
            const locationVal = filterValues.get('location');
            const locationMatch = !locationVal || data[5] === locationVal || data[6] === locationVal;
            return oilTypeMatch && locationMatch;
        });

        this.table.draw();
        $.fn.dataTable.ext.search.pop();
    }

    async handleOperationSelect(event) {
        const button = event.currentTarget;
        const operationData = JSON.parse(button.getAttribute('data-operation'));
        
        try {
            await this.fetchAndUpdateOperation(operationData);
            utils.cleanupModal('operationsModal');
            
            await Swal.fire({
                title: 'تم',
                text: 'تم اختيار العملية بنجاح',
                icon: 'success',
                timer: 1500,
                showConfirmButton: false
            });
        } catch (error) {
            logger.error('Error in operation selection:', error);
            await Swal.fire({
                title: 'خطأ',
                text: 'حدث خطأ أثناء اختيار العملية',
                icon: 'error'
            });
        }
    }

    async fetchAndUpdateOperation(operationData) {
        const response = await fetch(`/accounts/api/operations/${operationData.type}/${operationData.id}/`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': this.csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        });

        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        this.updateFormFields(data);
    }

    updateFormFields(data) {
        const fieldMappings = {
            'id_operation_id': 'id',
            'id_client': 'client',
            'id_oil_type': 'oil_type',
            'id_driver': 'driver',
            'id_quantity': 'quantity',
            'id_loading_location': 'loading_location',
            'id_unloading_location': 'unloading_location'
        };

        Object.entries(fieldMappings).forEach(([fieldId, dataKey]) => {
            const element = document.getElementById(fieldId);
            if (!element) return;

            const value = data[dataKey] || '';
            
            if (element.tagName === 'SELECT') {
                const $select = $(element);
                if ($select.data('select2')) {
                    if (value && !$select.find(`option[value='${value}']`).length) {
                        const newOption = new Option(data[`${dataKey}_name`], value, true, true);
                        $select.append(newOption);
                    }
                    $select.val(value).trigger('change');
                } else {
                    element.value = value;
                }
            } else {
                element.value = value;
            }
        });

        // Trigger any necessary dependent field updates
        $('#id_driver').trigger('change');
    }

    cleanup() {
        if (this.table) {
            this.table.destroy();
            this.table = null;
        }
        this.filters.clear();
    }
}

// Function to show operation selection modal - redirects to vehicle_movement.js implementation
function showOperationSelectionModal(operationType) {
    if (!operationType) {
        Swal.fire({
            title: 'خطأ',
            text: 'يرجى اختيار نوع العملية أولاً',
            icon: 'error'
        });
        return;
    }
    
    logger.debug('Showing operation selection modal for type:', operationType);
    
    // Use the implementation in vehicle_movement.js if available
    if (typeof window.vehicleMovementShowOperationsList === 'function') {
        window.vehicleMovementShowOperationsList(operationType);
    } else {
        // Fallback to local implementation
        showOperationsList(operationType);
    }
}

// Initialize on document ready
document.addEventListener('DOMContentLoaded', () => {
    const handler = new OperationsHandler();
    handler.init();

    const modal = document.getElementById('operationsModal');
    modal?.addEventListener('hidden.bs.modal', () => {
        handler.cleanup();
        modal.remove();
    });
});