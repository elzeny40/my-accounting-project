from django.db import models
from django.utils import timezone
from django.db import transaction

class VehicleMovement(models.Model):
    MOVEMENT_TYPES = [
        ('internal', 'داخلية'),
        ('external', 'خارجية'),
    ]
    
    OPERATION_TYPES = [
        ('sale', 'مبيعات'),
        ('purchase', 'مشتريات'),
    ]
    
    movement_id = models.CharField('رقم الحركة', max_length=50, primary_key=True)
    movement_type = models.CharField('نوع الحركة', max_length=10, choices=MOVEMENT_TYPES, default='external')
    operation_type = models.CharField('نوع العملية', max_length=10, choices=OPERATION_TYPES, null=True, blank=True)
    operation_id = models.CharField('رقم العملية', max_length=20, null=True, blank=True)
    date = models.DateField()
    client = models.ForeignKey('Client', on_delete=models.CASCADE, verbose_name='العميل')
    oil_type = models.ForeignKey('OilType', on_delete=models.CASCADE, verbose_name='نوع الزيت')
    quantity = models.DecimalField('الكمية', max_digits=10, decimal_places=3)
    driver = models.ForeignKey('Driver', on_delete=models.CASCADE, verbose_name='السائق')
    vehicle_number = models.CharField('رقم السيارة', max_length=20)
    loading_location = models.CharField('مكان التحميل', max_length=100)
    unloading_location = models.CharField('مكان التفريغ', max_length=100)
    driver_freight = models.DecimalField('نولون السائق', max_digits=10, decimal_places=2, null=True, blank=True)
    client_freight = models.DecimalField('نولون العميل', max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    updated_at = models.DateTimeField('تاريخ التحديث', auto_now=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.CASCADE, null=True, blank=True, verbose_name='تم الإنشاء بواسطة')

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'حركة سيارة'
        verbose_name_plural = 'حركات السيارات'
        
    def __str__(self):
        return f"{self.movement_id} - {self.client.name}"

    def save(self, *args, **kwargs):
        # التأكد من صحة النولون
        if self.driver_freight and self.client_freight:
            if self.driver_freight > self.client_freight:
                raise ValueError("نولون السائق لا يمكن أن يتجاوز نولون العميل")
        
        super().save(*args, **kwargs)