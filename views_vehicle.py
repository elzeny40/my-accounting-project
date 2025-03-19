from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from datetime import datetime
import logging

from .models_vehicle import VehicleMovement
from .models import Sale, Purchase, Driver
from .forms import VehicleMovementForm
from .mixins import AdminRequiredMixin

logger = logging.getLogger(__name__)

class VehicleMovementListView(LoginRequiredMixin, ListView):
    model = VehicleMovement
    template_name = 'accounts/vehicle_movement_list.html'
    context_object_name = 'movements'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = VehicleMovement.objects.select_related(
            'client', 
            'driver',
            'oil_type'
        ).order_by('-date', '-created_at')
        
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(movement_id__icontains=search_query) |
                Q(client__name__icontains=search_query) |
                Q(driver__name__icontains=search_query) |
                Q(vehicle_number__icontains=search_query)
            )
            
        movement_type = self.request.GET.get('type')
        if movement_type in ['internal', 'external']:
            queryset = queryset.filter(movement_type=movement_type)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['movement_type_filter'] = self.request.GET.get('type', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context

class VehicleMovementCreateView(LoginRequiredMixin, CreateView):
    model = VehicleMovement
    form_class = VehicleMovementForm
    template_name = 'accounts/vehicle_movement_form.html'
    success_url = reverse_lazy('vehicle_movement_list')
    
    def get_initial(self):
        initial = super().get_initial()
        initial['movement_type'] = self.kwargs.get('movement_type', 'external')
        initial['date'] = datetime.now().date()
        return initial
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = True
        context['movement_type'] = self.kwargs.get('movement_type', 'external')
        context['movement_type_display'] = 'داخلية' if context['movement_type'] == 'internal' else 'خارجية'
        return context

    def form_valid(self, form):
        try:
            form.instance.created_by = self.request.user
            
            # التحقق من النولون
            if form.cleaned_data.get('driver_freight') and form.cleaned_data.get('client_freight'):
                if form.cleaned_data['driver_freight'] > form.cleaned_data['client_freight']:
                    form.add_error('driver_freight', 'نولون السائق لا يمكن أن يتجاوز نولون العميل')
                    form.add_error('client_freight', 'نولون العميل يجب أن يكون أكبر من أو يساوي نولون السائق')
                    return self.form_invalid(form)
            
            # إنشاء رقم الحركة
            prefix = 'VEi-' if form.instance.movement_type == 'internal' else 'VEe-'
            last_movement = VehicleMovement.objects.filter(
                movement_id__startswith=prefix
            ).order_by('-movement_id').first()
            
            if last_movement:
                try:
                    last_number = int(last_movement.movement_id.split('-')[1])
                    next_number = last_number + 1
                except (IndexError, ValueError):
                    next_number = 1
            else:
                next_number = 1
                
            form.instance.movement_id = f'{prefix}{next_number:03d}'
            response = super().form_valid(form)
            messages.success(self.request, "تم إنشاء الحركة بنجاح")
            return response
            
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"Error creating vehicle movement: {str(e)}")
            messages.error(self.request, "حدث خطأ أثناء إنشاء الحركة")
            return self.form_invalid(form)

class VehicleMovementUpdateView(LoginRequiredMixin, UpdateView):
    model = VehicleMovement
    form_class = VehicleMovementForm
    template_name = 'accounts/vehicle_movement_form.html'
    success_url = reverse_lazy('vehicle_movement_list')
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        try:
            # التحقق من النولون
            if form.cleaned_data.get('driver_freight') and form.cleaned_data.get('client_freight'):
                if form.cleaned_data['driver_freight'] > form.cleaned_data['client_freight']:
                    form.add_error('driver_freight', 'نولون السائق لا يمكن أن يتجاوز نولون العميل')
                    form.add_error('client_freight', 'نولون العميل يجب أن يكون أكبر من أو يساوي نولون السائق')
                    return self.form_invalid(form)
            
            response = super().form_valid(form)
            messages.success(self.request, "تم تحديث الحركة بنجاح")
            return response
            
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"Error updating vehicle movement: {str(e)}")
            messages.error(self.request, "حدث خطأ أثناء تحديث الحركة")
            return self.form_invalid(form)

class VehicleMovementDetailView(LoginRequiredMixin, DetailView):
    model = VehicleMovement
    template_name = 'accounts/vehicle_movement_detail.html'
    context_object_name = 'movement'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movement = self.get_object()
        
        # إضافة تفاصيل العملية المرتبطة إذا كانت حركة داخلية
        if movement.movement_type == 'internal' and movement.operation_type:
            if movement.operation_type == 'sale':
                try:
                    context['related_operation'] = Sale.objects.get(id=movement.operation_id)
                except Sale.DoesNotExist:
                    pass
            elif movement.operation_type == 'purchase':
                try:
                    context['related_operation'] = Purchase.objects.get(id=movement.operation_id)
                except Purchase.DoesNotExist:
                    pass
                    
        return context

class VehicleMovementDeleteView(LoginRequiredMixin, DeleteView):
    model = VehicleMovement
    template_name = 'accounts/vehicle_movement_confirm_delete.html'
    success_url = reverse_lazy('vehicle_movement_list')
    pk_url_kwarg = 'pk'
    
    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(request, "تم حذف الحركة بنجاح")
            return response
        except Exception as e:
            logger.error(f"Error deleting vehicle movement: {str(e)}")
            messages.error(request, "حدث خطأ أثناء حذف الحركة")
            return self.get(request, *args, **kwargs)

# API Views
def get_driver_vehicle(request, driver_id):
    """إرجاع رقم سيارة السائق"""
    driver = get_object_or_404(Driver, id=driver_id)
    return JsonResponse({
        'vehicle_number': driver.vehicle_number
    })

def calculate_freight(request):
    """حساب النولون بناءً على الكمية"""
    try:
        quantity = float(request.GET.get('quantity', 0))
        client_id = request.GET.get('client_id')
        
        if not quantity or not client_id:
            return JsonResponse({
                'error': 'الكمية ورقم العميل مطلوبان'
            }, status=400)
            
        # هنا يمكن إضافة منطق حساب النولون حسب متطلبات العمل
        # مثال بسيط: النولون = الكمية × 10
        freight = quantity * 10
        
        return JsonResponse({
            'freight': freight
        })
    except ValueError:
        return JsonResponse({
            'error': 'قيمة الكمية غير صحيحة'
        }, status=400)
    except Exception as e:
        logger.error(f"Error calculating freight: {str(e)}")
        return JsonResponse({
            'error': 'حدث خطأ أثناء حساب النولون'
        }, status=500)


from django.http import HttpResponse
import csv
import xlwt
from django.contrib.auth.decorators import login_required

@login_required
def vehicle_movement_export(request):
    """تصدير حركات السيارات إلى ملف Excel أو PDF"""
    format_type = request.GET.get('format', 'excel')
    
    # الحصول على جميع حركات السيارات
    movements = VehicleMovement.objects.select_related(
        'client', 'driver', 'oil_type'
    ).order_by('-date', '-created_at')
    
    # تصدير إلى Excel
    if format_type == 'excel':
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="vehicle_movements.xls"'
        
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('حركات السيارات')
        
        # تنسيق العناوين
        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        
        # كتابة العناوين
        columns = [
            'رقم الحركة', 'التاريخ', 'نوع الحركة', 'رقم العملية', 'العميل', 'السائق',
            'رقم السيارة', 'نوع الزيت', 'الكمية', 'مكان التحميل', 'مكان التفريغ',
            'النولون للسائق', 'النولون للعميل'
        ]
        
        for col_num, column_title in enumerate(columns):
            ws.write(0, col_num, column_title, font_style)
        
        # كتابة البيانات
        for row_num, movement in enumerate(movements, 1):
            movement_type = 'داخلية' if movement.movement_type == 'internal' else 'خارجية'
            operation_id = movement.operation_id if movement.movement_type == 'internal' else '-'
            
            row = [
                movement.movement_id,
                movement.date.strftime('%Y-%m-%d'),
                movement_type,
                operation_id,
                movement.client.name,
                movement.driver.name,
                movement.vehicle_number,
                movement.oil_type.name,
                movement.quantity,
                movement.loading_location,
                movement.unloading_location,
                movement.driver_freight,
                movement.client_freight
            ]
            
            for col_num, cell_value in enumerate(row):
                ws.write(row_num, col_num, cell_value)
        
        wb.save(response)
        return response
        
    # تصدير إلى PDF
    elif format_type == 'pdf':
        # يمكن استخدام مكتبة مثل ReportLab أو WeasyPrint لإنشاء ملفات PDF
        # هذا مثال بسيط يعيد استجابة نصية
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="vehicle_movements.txt"'
        
        writer = csv.writer(response)
        writer.writerow([
            'رقم الحركة', 'التاريخ', 'نوع الحركة', 'رقم العملية', 'العميل', 'السائق',
            'رقم السيارة', 'نوع الزيت', 'الكمية', 'مكان التحميل', 'مكان التفريغ',
            'النولون للسائق', 'النولون للعميل'
        ])
        
        for movement in movements:
            movement_type = 'داخلية' if movement.movement_type == 'internal' else 'خارجية'
            operation_id = movement.operation_id if movement.movement_type == 'internal' else '-'
            
            writer.writerow([
                movement.movement_id,
                movement.date.strftime('%Y-%m-%d'),
                movement_type,
                operation_id,
                movement.client.name,
                movement.driver.name,
                movement.vehicle_number,
                movement.oil_type.name,
                movement.quantity,
                movement.loading_location,
                movement.unloading_location,
                movement.driver_freight,
                movement.client_freight
            ])
        
        return response
    
    # إذا لم يتم تحديد نوع صالح
    return HttpResponse("نوع التصدير غير صالح", status=400)