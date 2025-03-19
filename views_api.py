from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from .models import Sale, Purchase, Driver, Client, OilType
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

@login_required
def get_operations_list(request, operation_type):
    """Returns a list of operations (sales or purchases) for selection in vehicle movement form"""
    logger.debug(f"Fetching operations list. Type: {operation_type}")
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        if operation_type == 'sale':
            logger.debug("Processing sale operations")
            queryset = Sale.objects.select_related('client', 'oil_type', 'driver').order_by('-date')[:100]
            operations = [{
                'id': sale.id,
                'date': sale.date.strftime('%Y-%m-%d'),
                'client': sale.client.id,
                'client_name': sale.client.name,
                'oil_type': sale.oil_type.id,
                'oil_type_name': sale.oil_type.name,
                'quantity': float(sale.quantity),
                'loading_location': sale.loading_location or '',
                'unloading_location': sale.unloading_location or '',
                'driver': sale.driver.id if sale.driver else None,
                'driver_name': sale.driver.name if sale.driver else '',
                'driver_freight': float(sale.driver_freight) if sale.driver_freight else 0,
                'client_freight': float(sale.client_freight) if sale.client_freight else 0
            } for sale in queryset]
            logger.debug(f"Found {len(operations)} sales operations")
            
        elif operation_type == 'purchase':
            logger.debug("Processing purchase operations")
            # تغيير طريقة استرجاع البيانات لتتوافق مع نموذج Purchase
            queryset = Purchase.objects.select_related('supplier', 'oil_type', 'driver').order_by('-date')[:100]
            operations = []
            
            for purchase in queryset:
                try:
                    # تسجيل معلومات تصحيح الأخطاء
                    logger.debug(f"Processing purchase ID: {purchase.id}")
                    
                    operations.append({
                        'id': purchase.id,
                        'date': purchase.date.strftime('%Y-%m-%d'),
                        'client': purchase.supplier.id,
                        'client_name': purchase.supplier.name,
                        'oil_type': purchase.oil_type.id,
                        'oil_type_name': purchase.oil_type.name,
                        'quantity': float(purchase.quantity),
                        'loading_location': purchase.loading_location or '',
                        'unloading_location': purchase.unloading_location or '',
                        'driver': purchase.driver.id if purchase.driver else None,
                        'driver_name': purchase.driver.name if purchase.driver else '',
                        'driver_freight': float(purchase.driver_freight) if purchase.driver_freight else 0,
                        'client_freight': float(purchase.client_freight) if purchase.client_freight else 0
                    })
                except Exception as e:
                    logger.error(f"Error processing purchase {purchase.id}: {str(e)}")
                    # استمر مع العملية التالية بدلاً من فشل الطلب بأكمله
            
            logger.debug(f"Found {len(operations)} purchase operations")
            
        else:
            logger.error(f"Invalid operation type: {operation_type}")
            return JsonResponse({'error': 'Invalid operation type'}, status=400)

        return JsonResponse({'operations': operations})
        
    except Exception as e:
        logger.error(f"Error in get_operations_list: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
def get_operation_details(request, operation_type, operation_id):
    """Returns details of a specific operation for populating vehicle movement form"""
    logger.debug(f"Fetching operation details. Type: {operation_type}, ID: {operation_id}")
    
    try:
        if operation_type == 'sale':
            operation = Sale.objects.select_related('client', 'oil_type', 'driver').get(id=operation_id)
            data = {
                'id': operation.id,
                'date': operation.date.strftime('%Y-%m-%d'),
                'client': operation.client.id,
                'client_name': operation.client.name,
                'oil_type': operation.oil_type.id,
                'oil_type_name': operation.oil_type.name,
                'quantity': float(operation.quantity),
                'loading_location': operation.loading_location or '',
                'unloading_location': operation.unloading_location or '',
                'driver': operation.driver.id if operation.driver else None,
                'driver_name': operation.driver.name if operation.driver else '',
                'driver_freight': float(operation.driver_freight) if operation.driver_freight else 0,
                'client_freight': float(operation.client_freight) if operation.client_freight else 0
            }
            
        elif operation_type == 'purchase':
            operation = Purchase.objects.select_related('supplier', 'oil_type', 'driver').get(id=operation_id)
            data = {
                'id': operation.id,
                'client': operation.supplier.id,
                'client_name': operation.supplier.name,
                'oil_type': operation.oil_type.id,
                'oil_type_name': operation.oil_type.name,
                'quantity': float(operation.quantity),
                'loading_location': operation.loading_location or '',
                'unloading_location': operation.unloading_location or '',
                'driver': operation.driver.id if operation.driver else None,
                'driver_name': operation.driver.name if operation.driver else '',
                'driver_freight': float(operation.driver_freight) if operation.driver_freight else 0,
                'client_freight': float(operation.client_freight) if operation.client_freight else 0
            }
        else:
            logger.error(f"Invalid operation type: {operation_type}")
            return JsonResponse({'error': 'Invalid operation type'}, status=400)

        logger.debug(f"Operation details found: {data}")
        return JsonResponse(data)
        
    except (Sale.DoesNotExist, Purchase.DoesNotExist) as e:
        logger.error(f"Operation not found: {str(e)}")
        return JsonResponse({'error': 'Operation not found'}, status=404)
    except Exception as e:
        logger.error(f"Error fetching operation details: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_driver_vehicle(request, driver_id):
    """Returns vehicle number for a driver"""
    try:
        driver = get_object_or_404(Driver, id=driver_id)
        return JsonResponse({
            'vehicle_number': driver.vehicle_number
        })
    except Exception as e:
        logger.error(f"Error fetching driver vehicle: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def calculate_freight(request):
    """Calculate freight based on quantity and client settings"""
    try:
        quantity = Decimal(request.GET.get('quantity', '0'))
        client_id = request.GET.get('client_id')
        
        if not quantity or not client_id:
            return JsonResponse({
                'error': 'الكمية ورقم العميل مطلوبان'
            }, status=400)
        
        client = get_object_or_404(Client, id=client_id)
        
        # حساب النولون حسب معدل العميل
        # يمكن إضافة منطق حساب أكثر تعقيداً هنا
        base_rate = Decimal('10.00')  # سعر النولون الأساسي لكل طن
        quantity_factor = Decimal('1.00')  # معامل الكمية
        
        if quantity > 20:
            quantity_factor = Decimal('0.95')  # خصم 5% للكميات الكبيرة
        elif quantity > 10:
            quantity_factor = Decimal('0.97')  # خصم 3% للكميات المتوسطة
            
        freight = quantity * base_rate * quantity_factor
        
        return JsonResponse({
            'freight': float(freight.quantize(Decimal('0.01'))),
            'base_rate': float(base_rate),
            'quantity_factor': float(quantity_factor)
        })
        
    except ValueError:
        return JsonResponse({
            'error': 'قيمة الكمية غير صحيحة'
        }, status=400)
    except Client.DoesNotExist:
        return JsonResponse({
            'error': 'العميل غير موجود'
        }, status=404)
    except Exception as e:
        logger.error(f"Error calculating freight: {str(e)}")
        return JsonResponse({
            'error': 'حدث خطأ أثناء حساب النولون'
        }, status=500)