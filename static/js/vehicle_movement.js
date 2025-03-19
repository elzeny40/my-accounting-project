// Initialize Select2 and setup form elements
function initializeFormElements() {
    // Initialize Select2 for all select elements
    $('.select2').select2({
        theme: 'bootstrap4',
        dir: 'rtl',
        language: 'ar'
    });

    // Initialize datepicker
    $('#id_date').datepicker({
        format: 'yyyy-mm-dd',
        autoclose: true,
        todayHighlight: true,
        rtl: true,
        language: 'ar'
    });

    // Set default date if empty
    if (!$('#id_date').val()) {
        $('#id_date').datepicker('setDate', new Date());
    }
}

// Setup event listeners for form interactions
function setupEventListeners() {
    // Show operations modal when button is clicked
    $('#showOperationsBtn').on('click', function() {
        showOperationsModal();
    });

    // Handle operation type change
    $('#id_operation_type').on('change', function() {
        const operationType = $(this).val();
        if (operationType) {
            fetchNextOperationId(operationType);
        }
    });

    // Handle driver selection
    $('#id_driver').on('change', function() {
        const driverId = $(this).val();
        if (driverId) {
            fetchDriverVehicle(driverId);
        }
    });

    // Handle client selection
    $('#id_client').on('change', function() {
        updateClientFreight();
    });

    // Handle quantity change
    $('#id_quantity').on('input', function() {
        updateClientFreight();
    });
}

// Fetch next operation ID based on operation type
function fetchNextOperationId(operationType) {
    $.ajax({
        url: '/api/next-operation-id/',
        data: { operation_type: operationType },
        success: function(response) {
            $('#id_operation_id').val(response.next_id);
        },
        error: function() {
            alert('حدث خطأ أثناء جلب رقم العملية');
        }
    });
}

// Fetch vehicle number for selected driver
function fetchDriverVehicle(driverId) {
    $.ajax({
        url: '/api/driver-vehicle/',
        data: { driver_id: driverId },
        success: function(response) {
            if (response.vehicle_number) {
                $('#id_vehicle_number').val(response.vehicle_number);
            }
        },
        error: function() {
            alert('حدث خطأ أثناء جلب رقم السيارة');
        }
    });
}

// Update client freight based on quantity and client
function updateClientFreight() {
    const clientId = $('#id_client').val();
    const quantity = $('#id_quantity').val();
    
    if (clientId && quantity) {
        $.ajax({
            url: '/api/calculate-freight/',
            data: {
                client_id: clientId,
                quantity: quantity
            },
            success: function(response) {
                $('#id_client_freight').val(response.freight);
            },
            error: function() {
                console.error('حدث خطأ أثناء حساب النولون');
            }
        });
    }
}

// Show operations modal for selection
function showOperationsModal() {
    const operationType = $('#id_operation_type').val();
    if (!operationType) {
        alert('الرجاء اختيار نوع العملية أولاً');
        return;
    }

    $.ajax({
        url: `/accounts/api/operations/${operationType}/list/`,
        data: { operation_type: operationType },
        success: function(response) {
            // Create and show modal with operations list
            const modalContent = createOperationsModalContent(response.operations);
            showModal('عمليات متاحة', modalContent);
        },
        error: function() {
            alert('حدث خطأ أثناء جلب قائمة العمليات');
        }
    });
}

// Create modal content for operations list
function createOperationsModalContent(operations) {
    let content = '<div class="table-responsive"><table class="table table-hover">'
        + '<thead><tr>'
        + '<th>رقم العملية</th>'
        + '<th>التاريخ</th>'
        + '<th>العميل</th>'
        + '<th>نوع الزيت</th>'
        + '<th>الكمية</th>'
        + '</tr></thead><tbody>';

    operations.forEach(op => {
        content += `<tr data-operation-id="${op.id}" onclick="selectOperation(${op.id})">`
            + `<td>${op.id}</td>`
            + `<td>${op.date}</td>`
            + `<td>${op.client_name}</td>`
            + `<td>${op.oil_type}</td>`
            + `<td>${op.quantity}</td>`
            + '</tr>';
    });

    content += '</tbody></table></div>';
    return content;
}

// Show modal with dynamic content
function showModal(title, content) {
    const modalHtml = `
        <div class="modal fade" id="dynamicModal" tabindex="-1" role="dialog">
            <div class="modal-dialog modal-lg" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">${content}</div>
                </div>
            </div>
        </div>`;

    // Remove existing modal if any
    $('#dynamicModal').remove();
    
    // Add new modal to body
    $('body').append(modalHtml);
    
    // Show modal
    $('#dynamicModal').modal('show');
}

// Handle operation selection from modal
function selectOperation(operationId) {
    const operationType = $('#id_operation_type').val();
    if (!operationType) {
        alert('حدث خطأ: نوع العملية غير محدد');
        return;
    }

    $.ajax({
        url: `/accounts/api/operations/${operationType}/${operationId}/`,
        success: function(response) {
            // Fill form fields with operation details
            $('#id_operation_id').val(response.id);
            $('#id_client').val(response.client).trigger('change');
            $('#id_oil_type').val(response.oil_type).trigger('change');
            $('#id_quantity').val(response.quantity);
            $('#id_loading_location').val(response.loading_location);
            $('#id_unloading_location').val(response.unloading_location);
            if (response.driver) {
                $('#id_driver').val(response.driver).trigger('change');
            }
            
            // Close modal
            $('#dynamicModal').modal('hide');
        },
        error: function() {
            alert('حدث خطأ أثناء جلب تفاصيل العملية');
        }
    });
}