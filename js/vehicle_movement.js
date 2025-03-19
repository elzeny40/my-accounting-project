/**
 * Vehicle Movement JavaScript Functions
 * Handles movement types, operation selection, and field management
 */

// Vehicle Movement Operations Handler
class VehicleMovementHandler {
    constructor() {
        this.operationType = '';
        this.csrfToken = this.getCookie('csrftoken');
        this.operationsTable = null;
        this.loadingTimeout = null;
    }

    init() {
        this.initializeFormElements();
        this.setupEventListeners();
        this.updateShowOperationsButton();
    }

    getCookie(name) {
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

    initializeFormElements() {
        // Set default date to today
        const dateInput = document.getElementById('id_date');
        if (dateInput && !dateInput.value) {
            const today = new Date().toISOString().split('T')[0];
            dateInput.value = today;
        }

        // Initialize Select2
        $('.select2').select2({
            theme: 'bootstrap-5',
            width: '100%',
            language: {
                noResults: () => "لا توجد نتائج"
            }
        });

        // Set default operation type
        const operationTypeInput = document.getElementById('id_operation_type');
        if (operationTypeInput && !operationTypeInput.value) {
            operationTypeInput.value = 'sale';
        }

        // Initialize quantity input for 3 decimal places
        const quantityInput = document.getElementById('id_quantity');
        if (quantityInput) {
            quantityInput.addEventListener('input', function(e) {
                let value = e.target.value;
                if (value.includes('.')) {
                    const parts = value.split('.');
                    if (parts[1].length > 3) {
                        e.target.value = parts[0] + '.' + parts[1].slice(0, 3);
                    }
                }
            });
        }
    }

    setupEventListeners() {
        const movementTypeSelect = document.getElementById('id_movement_type');
        const operationTypeSelect = document.getElementById('id_operation_type');
        const showOperationsBtn = document.getElementById('showOperationsBtn');
        const operationFields = document.getElementById('operation-fields');
        const vehicleMovementForm = document.getElementById('vehicleMovementForm');

        // Handle form submission
        if (vehicleMovementForm) {
            vehicleMovementForm.addEventListener('submit', (e) => {
                // Validate freight before submitting
                if (!this.validateFreight()) {
                    e.preventDefault();
                    return false;
                }
                
                // Additional validations
                const requiredFields = {
                    'id_client': 'العميل',
                    'id_oil_type': 'نوع الزيت',
                    'id_quantity': 'الكمية',
                    'id_driver': 'السائق',
                    'id_vehicle_number': 'رقم السيارة',
                    'id_loading_location': 'مكان التحميل',
                    'id_unloading_location': 'مكان التفريغ'
                };
                
                let isValid = true;
                let firstInvalidField = null;
                
                // Check all required fields
                Object.entries(requiredFields).forEach(([id, label]) => {
                    const field = document.getElementById(id);
                    if (!field || !field.value.trim()) {
                        isValid = false;
                        if (!firstInvalidField) firstInvalidField = field;
                        
                        // Add visual indication
                        field.classList.add('is-invalid');
                        
                        // Add error message if not exists
                        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
                        if (!errorDiv) {
                            const div = document.createElement('div');
                            div.className = 'invalid-feedback';
                            div.textContent = `حقل ${label} مطلوب`;
                            field.parentNode.appendChild(div);
                        }
                    } else {
                        field.classList.remove('is-invalid');
                        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
                        if (errorDiv) errorDiv.remove();
                    }
                });
                
                if (!isValid) {
                    e.preventDefault();
                    if (firstInvalidField) firstInvalidField.focus();
                    
                    Swal.fire({
                        title: 'خطأ',
                        text: 'يرجى ملء جميع الحقول المطلوبة',
                        icon: 'error'
                    });
                    
                    return false;
                }
                
                // Form is valid, allow submission
                return true;
            });
        }

        // Handle movement type change
        if (movementTypeSelect) {
            movementTypeSelect.addEventListener('change', function() {
                const isInternal = this.value === 'internal';
                if (operationFields) {
                    operationFields.classList.toggle('d-none', !isInternal);
                }
                if (operationTypeSelect) {
                    operationTypeSelect.disabled = !isInternal;
                    if (!isInternal) {
                        operationTypeSelect.value = '';
                        operationTypeSelect.dispatchEvent(new Event('change'));
                    }
                }
                vehicleMovement.updateShowOperationsButton();
            });
        }

        // Handle operation type change
        if (operationTypeSelect) {
            operationTypeSelect.addEventListener('change', function() {
                // Add a small delay to ensure select2 has fully initialized
                setTimeout(() => {
                    vehicleMovement.updateShowOperationsButton();
                    if (!this.value) {
                        vehicleMovement.clearFormFields();
                    }
                }, 200);
            });
        }

        // Handle show operations button click
        if (showOperationsBtn) {
            showOperationsBtn.addEventListener('click', function() {
                const operationType = operationTypeSelect.value;
                if (!operationType) {
                    Swal.fire({
                        title: 'خطأ',
                        text: 'يرجى اختيار نوع العملية أولاً',
                        icon: 'error'
                    });
                    return;
                }

                // Show loading state
                showOperationsBtn.disabled = true;
                showOperationsBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>جاري التحميل...';

                // Fetch operations
                vehicleMovement.loadOperations(operationType);
            });
        }

        // Driver change event
        $('#id_driver').on('change', () => this.updateVehicleNumber());

        // Client and quantity change events
        $('#id_client, #id_quantity').on('change input', () => this.calculateFreight());
    }

    handleError(error, title = 'خطأ', customMessage = null) {
        console.error('Error:', error);
        Swal.fire({
            title: title,
            text: customMessage || 'حدث خطأ أثناء تنفيذ العملية',
            icon: 'error'
        });
    }

    showLoading(message = 'جاري التحميل...') {
        return Swal.fire({
            title: message,
            allowOutsideClick: false,
            showConfirmButton: false,
            willOpen: () => {
                Swal.showLoading();
            }
        });
    }

    async loadOperations(type) {
        const loadingSwal = this.showLoading();
        const showOperationsBtn = document.getElementById('showOperationsBtn');
        
        try {
            console.log(`[DEBUG] Loading operations of type: ${type}`);
            const response = await fetch(`/accounts/api/operations/${type}/list/`);
            
            if (!response.ok) {
                console.error(`[ERROR] HTTP error! status: ${response.status}`);
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log(`[DEBUG] Received ${data.operations?.length || 0} operations`);
            
            loadingSwal.close();
            
            if (!data.operations || data.operations.length === 0) {
                Swal.fire({
                    title: 'تنبيه',
                    text: 'لا توجد عمليات متاحة',
                    icon: 'info'
                });
                return;
            }
            
            this.showOperationsModal(data.operations, type);
        } catch (error) {
            console.error('[ERROR] Failed to load operations:', error);
            loadingSwal.close();
            this.handleError(error, 'خطأ', 'حدث خطأ أثناء تحميل العمليات');
        } finally {
            // إعادة تفعيل الزر
            if (showOperationsBtn) {
                showOperationsBtn.disabled = false;
                showOperationsBtn.innerHTML = '<i class="fas fa-list-ul me-1"></i>عرض العمليات المتاحة';
            }
        }
    }

    async selectOperation(operationId, type) {
        const loadingSwal = this.showLoading('جاري تحميل بيانات العملية...');
        
        try {
            const response = await fetch(`/accounts/api/operations/${type}/${operationId}/`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            this.fillFormFields(data);
            loadingSwal.close();

            Swal.fire({
                title: 'تم',
                text: 'تم اختيار العملية بنجاح',
                icon: 'success',
                timer: 1500,
                showConfirmButton: false
            });
        } catch (error) {
            loadingSwal.close();
            this.handleError(error, 'خطأ', 'حدث خطأ أثناء جلب تفاصيل العملية');
        }
    }

    fillFormFields(data) {
        const fields = {
            'id_client': { value: data.client, trigger: true },
            'id_oil_type': { value: data.oil_type, trigger: true },
            'id_quantity': { value: data.quantity },
            'id_loading_location': { value: data.loading_location },
            'id_unloading_location': { value: data.unloading_location },
            'id_driver': { value: data.driver, trigger: true },
            'id_vehicle_number': { value: data.vehicle_number || '' },
            'id_driver_freight': { value: data.driver_freight || 0 },
            'id_client_freight': { value: data.client_freight || 0 }
        };

        Object.entries(fields).forEach(([id, config]) => {
            const element = $(`#${id}`);
            if (element.length) {
                element.val(config.value);
                if (config.trigger) element.trigger('change');
            }
        });
        
        // تحديث حقول العملية
        $('#id_operation_id').val(data.id);
        const operationType = $('#id_operation_type').val();
        if (operationType) {
            console.log(`[DEBUG] Setting operation details: Type=${operationType}, ID=${data.id}`);
        }
    }

    async updateVehicleNumber() {
        const driverId = $('#id_driver').val();
        if (!driverId) {
            $('#id_vehicle_number').val('');
            return;
        }

        try {
            const response = await fetch(`/accounts/api/drivers/${driverId}/vehicle/`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            $('#id_vehicle_number').val(data.vehicle_number || '');
        } catch (error) {
            this.handleError(error, 'خطأ', 'حدث خطأ أثناء جلب رقم السيارة');
            $('#id_vehicle_number').val('');
        }
    }

    async calculateFreight() {
        const clientId = $('#id_client').val();
        const quantity = $('#id_quantity').val();
        
        if (!clientId || !quantity) return;

        // Add debounce to avoid too many requests
        clearTimeout(this.loadingTimeout);
        this.loadingTimeout = setTimeout(async () => {
            try {
                const response = await fetch(
                    `/accounts/api/calculate-freight/?client_id=${clientId}&quantity=${quantity}`
                );
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                
                const data = await response.json();
                if (data.freight) {
                    $('#id_client_freight').val(data.freight.toFixed(2));
                    
                    // Update driver freight if empty (70% of client freight by default)
                    const driverFreight = $('#id_driver_freight').val();
                    if (!driverFreight) {
                        $('#id_driver_freight').val((data.freight * 0.7).toFixed(2));
                    }
                }
            } catch (error) {
                this.handleError(error, 'خطأ', 'حدث خطأ أثناء حساب النولون');
            }
        }, 500);
    }

    validateFreight() {
        const driverFreight = parseFloat($('#id_driver_freight').val()) || 0;
        const clientFreight = parseFloat($('#id_client_freight').val()) || 0;
        
        if (driverFreight > clientFreight) {
            Swal.fire({
                title: 'تحذير',
                text: 'نولون السائق لا يمكن أن يتجاوز نولون العميل',
                icon: 'warning'
            });
            return false;
        }
        return true;
    }

    updateShowOperationsButton() {
        const showOperationsBtn = document.getElementById('showOperationsBtn');
        const operationTypeSelect = document.getElementById('id_operation_type');
        
        if (showOperationsBtn) {
            const hasOperationType = operationTypeSelect?.value;
            showOperationsBtn.disabled = !hasOperationType;
            
            // Update button text
            showOperationsBtn.innerHTML = `
                <i class="fas fa-list-ul me-1"></i>
                عرض العمليات المتاحة
            `;
            
            // Log the button state for debugging
            console.log('[DEBUG] Show operations button state updated:', { 
                operationType: operationTypeSelect?.value,
                isDisabled: showOperationsBtn.disabled 
            });
        }
    }

    showOperationsModal(data, operationType) {
        // Use the existing modal in the DOM
        const modalElement = document.getElementById('operationsModal');
        const modalTitle = modalElement.querySelector('.modal-title');
        const modalBody = modalElement.querySelector('#operationsTableContainer');
        
        // Set the title based on operation type
        modalTitle.textContent = operationType === 'sale' ? 'عمليات البيع' : 'عمليات الشراء';
        
        // Create the table HTML
        modalBody.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover" id="operationsTable">
                    <thead>
                        <tr>
                            <th>رقم العملية</th>
                            <th>التاريخ</th>
                            <th>العميل</th>
                            <th>نوع الزيت</th>
                            <th>الكمية</th>
                            <th>موقع التحميل</th>
                            <th>موقع التفريغ</th>
                            <th>السائق</th>
                            <th>اختيار</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.createOperationsTableRows(data)}
                    </tbody>
                </table>
            </div>
        `;
        
        // Setup search functionality
        const searchInput = document.getElementById('operationsSearch');
        if (searchInput) {
            searchInput.value = ''; // Clear previous search
            searchInput.addEventListener('input', function() {
                const searchValue = this.value.toLowerCase();
                const rows = document.querySelectorAll('#operationsTable tbody tr');
                
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchValue) ? '' : 'none';
                });
            });
        }
        
        // Handle operation selection
        modalBody.querySelectorAll('.select-operation').forEach(btn => {
            btn.addEventListener('click', () => {
                const operationId = btn.dataset.id;
                this.selectOperation(operationId, operationType);
                bootstrap.Modal.getInstance(modalElement).hide();
            });
        });
        
        // Show the modal
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }

    // createOperationsModal method removed as we're using the existing modal in the DOM

    createOperationsTableRows(operations) {
        return operations.map(op => `
            <tr>
                <td>${op.id}</td>
                <td>${this.formatDate(op.date)}</td>
                <td>${op.client_name}</td>
                <td>${op.oil_type_name}</td>
                <td>${op.quantity}</td>
                <td>${op.loading_location || '-'}</td>
                <td>${op.unloading_location || '-'}</td>
                <td>${op.driver_name || '-'}</td>
                <td>
                    <button type="button" class="btn btn-sm btn-primary select-operation" data-id="${op.id}">
                        <i class="fas fa-check"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ar-EG');
    }

    clearFormFields() {
        document.getElementById('id_operation_id').value = '';
        document.getElementById('id_client').value = '';
        document.getElementById('id_oil_type').value = '';
        document.getElementById('id_quantity').value = '';
        document.getElementById('id_driver').value = '';
        document.getElementById('id_vehicle_number').value = '';
        document.getElementById('id_loading_location').value = '';
        document.getElementById('id_unloading_location').value = '';
        document.getElementById('id_driver_freight').value = '';
        document.getElementById('id_client_freight').value = '';
        
        // Trigger change events for select2
        $('#id_client, #id_oil_type, #id_driver').trigger('change');
    }
}

// Initialize handler
const vehicleMovement = new VehicleMovementHandler();
document.addEventListener('DOMContentLoaded', () => vehicleMovement.init());

// Expose methods for global access (backward compatibility)
window.vehicleMovementShowOperationsList = (type) => vehicleMovement.loadOperations(type);
window.vehicleMovementSelectOperation = (id, type) => vehicleMovement.selectOperation(id, type);