from django.contrib.auth.models import AbstractUser, Group
import datetime
from django.db import models, transaction
from django.db.models import Max
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('user', 'Regular User'),
        ('client_manager', 'مدير العملاء'),
        ('reports_viewer', 'مشاهد التقارير'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class ActivityLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"

class Driver(models.Model):
    driver_id = models.CharField(max_length=10, unique=True, editable=False)
    name = models.CharField(default='', max_length=200, verbose_name='إسم السائق')
    id_number = models.CharField(default='', max_length=20, verbose_name='رقم البطاقة')
    address = models.TextField(default='', verbose_name='العنوان')
    phone_number = models.CharField(default='', max_length=11, validators=[RegexValidator(regex='^01[0125][0-9]{8}$', message='رقم الهاتف يجب أن يكون بصيغة أرقام مصرية (مثال: 01012345678)')], verbose_name='رقم التليفون')
    license_number = models.CharField(max_length=20, verbose_name='رقم الرخصة')
    license_type = models.CharField(choices=[('first', 'أولى'), ('second', 'ثانية'), ('third', 'ثالثة')], default='first', max_length=10, verbose_name='نوع الرخصة')
    license_expiry_date = models.DateField(blank=True, null=True, verbose_name='تاريخ انتهاء الرخصة')
    vehicle_number = models.CharField(default='', max_length=20, verbose_name='رقم السيارة')
    vehicle_type = models.CharField(default='', max_length=50, verbose_name='نوع السيارة')
    hire_date = models.DateField(auto_now_add=True, verbose_name='تاريخ التعيين')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='الرصيد')
    
    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.driver_id:
            # Get the highest driver_id number with a lock
            last_driver = Driver.objects.select_for_update().order_by('-driver_id').first()
            if last_driver:
                # Extract the number from the last driver_id and increment it
                try:
                    last_number = int(last_driver.driver_id.split('-')[1])
                    new_number = last_number + 1
                except (IndexError, ValueError):
                    new_number = 1
            else:
                new_number = 1
            # Format the new driver_id with leading zeros
            self.driver_id = f'DR-{new_number:03d}'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} - {self.license_number}"



class OilType(models.Model):
    id = models.CharField(editable=False, max_length=10, primary_key=True, serialize=False)
    name = models.CharField(max_length=100)
    properties = models.TextField()
    notes = models.TextField(blank=True)
    price_per_liter = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_quantity = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.id:
            last_oil = OilType.objects.select_for_update().order_by('-id').first()
            if last_oil:
                try:
                    last_number = int(last_oil.id.split('-')[1])
                    new_number = last_number + 1
                except (IndexError, ValueError):
                    new_number = 1
            else:
                new_number = 1
            self.id = f'OT-{new_number:03d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name





class Client(models.Model):
    client_id = models.CharField(max_length=10, unique=True, editable=False)
    name = models.CharField(max_length=200)
    company_name = models.CharField(blank=True, max_length=200, null=True)
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    commercial_reg_number = models.CharField(blank=True, max_length=50, null=True)
    bank_account_number = models.CharField(blank=True, max_length=50, null=True)
    balance = models.DecimalField(decimal_places=2, default=0, max_digits=10)
    created_at = models.DateTimeField(default=timezone.now)

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.client_id:
            # Get the highest client_id number with a lock
            last_client = Client.objects.select_for_update().order_by('-client_id').first()
            if last_client:
                # Extract the number from the last client_id and increment it
                try:
                    last_number = int(last_client.client_id.split('-')[1])
                    new_number = last_number + 1
                except (IndexError, ValueError):
                    new_number = 1
            else:
                new_number = 1
            # Format the new client_id with leading zeros
            self.client_id = f'CL-{new_number:03d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.client_id})"



class Sale(models.Model):
    sale_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    date = models.DateField()
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    oil_type = models.ForeignKey('OilType', on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    loading_location = models.CharField(max_length=100, default='', blank=True)
    unloading_location = models.CharField(max_length=100, default='', blank=True)
    driver = models.ForeignKey('Driver', on_delete=models.PROTECT, null=True, blank=True)
    vehicle_number = models.CharField(max_length=20, blank=True, null=True)
    driver_freight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    client_freight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    
    def clean(self):
        if self.driver_freight and self.client_freight:
            if self.driver_freight > self.client_freight:
                raise ValidationError({
                    'driver_freight': 'نولون السائق لا يمكن أن يتجاوز نولون العميل',
                    'client_freight': 'نولون العميل يجب أن يكون أكبر من أو يساوي نولون السائق'
                })

    def save(self, *args, **kwargs):
        self.clean()
        self.amount = self.quantity * self.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sale_id} - {self.client.name}"

    class Meta:
        ordering = ['-date']
        verbose_name = 'عملية بيع'
        verbose_name_plural = 'عمليات البيع'

class Treasury(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'وارد'),
        ('expense', 'منصرف')
    ]
    PAYMENT_METHODS = [
        ('cash', 'نقدي'),
        ('check', 'شيك'),
        ('transfer', 'تحويل'),
        ('other', 'أخرى')
    ]
    MOVEMENT_SOURCES = [
        ('client_account', 'حساب عميل'),
        ('company_account', 'حساب شركة'),
        ('driver_account', 'حساب سائق'),
        ('direct_deposit', 'إيداع مباشر')
    ]
    
    movement_id = models.AutoField(primary_key=True, verbose_name='رقم الحركة')
    date = models.DateField()
    description = models.TextField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    movement_source = models.CharField(max_length=20, choices=MOVEMENT_SOURCES)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_details = models.CharField(max_length=100, blank=True, null=True)
    related_sale = models.ForeignKey('Sale', on_delete=models.SET_NULL, null=True, blank=True)
    related_purchase = models.ForeignKey('Purchase', on_delete=models.SET_NULL, related_name='treasury_movements', null=True, blank=True)
    related_driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, related_name='treasury_movements', null=True, blank=True)
    related_client = models.ForeignKey(Client, on_delete=models.SET_NULL, related_name='treasury_movements', null=True, blank=True)
    oil_type = models.ForeignKey(OilType, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total = models.DecimalField(max_digits=15, decimal_places=2, editable=False, null=True, blank=True)
    
    def __str__(self):
        if self.related_client:
            return f"{self.movement_id} - {self.related_client.name}"
        elif self.related_driver:
            return f"{self.movement_id} - {self.related_driver.name}"
        else:
            return f"{self.movement_id}"

class Purchase(models.Model):
    BU_ID = models.CharField(max_length=20, unique=True, editable=False)
    date = models.DateField()
    supplier = models.ForeignKey('Client', on_delete=models.CASCADE, null=True, blank=True)
    oil_type = models.ForeignKey('OilType', on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    loading_location = models.CharField(max_length=200)
    unloading_location = models.CharField(max_length=200)
    driver = models.ForeignKey('Driver', on_delete=models.PROTECT, null=True, blank=True)
    vehicle_number = models.CharField(max_length=20, blank=True, null=True)
    driver_freight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    client_freight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)

    def clean(self):
        if self.driver_freight and self.client_freight:
            if self.driver_freight > self.client_freight:
                raise ValidationError({
                    'driver_freight': 'نولون السائق لا يمكن أن يتجاوز نولون العميل',
                    'client_freight': 'نولون العميل يجب أن يكون أكبر من أو يساوي نولون السائق'
                })

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.clean()
        creating = not self.pk
        self.amount = self.quantity * self.price
        
        if not self.BU_ID:
            last_purchase = Purchase.objects.select_for_update().order_by('-BU_ID').first()
            if last_purchase:
                try:
                    last_number = int(last_purchase.BU_ID.split('-')[1])
                    new_number = last_number + 1
                except (IndexError, ValueError):
                    new_number = 1
            else:
                new_number = 1
            self.BU_ID = f'BU-{new_number:03d}'
            
        super().save(*args, **kwargs)

    def __str__(self):
        supplier_name = self.supplier.name if self.supplier else 'بدون مورد'
        return f"{self.BU_ID} - {supplier_name}"

    class Meta:
        ordering = ['-date']
        verbose_name = 'عملية شراء'
        verbose_name_plural = 'عمليات الشراء'

class CompanyAccount(models.Model):
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    name = models.CharField(max_length=100, default='الحساب الرئيسي')
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f'{self.name} - الرصيد: {self.balance}'

class BalanceChangeLog(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='balance_changes')
    previous_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    new_balance = models.DecimalField(max_digits=15, decimal_places=2)
    change_amount = models.DecimalField(max_digits=15, decimal_places=2)
    notes = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.client:
            return f"{self.client.name} balance changed from {self.previous_balance} to {self.new_balance}"
        elif self.driver:
            return f"Client balance changed from {self.previous_balance} to {self.new_balance}"
        return f"Balance changed from {self.previous_balance} to {self.new_balance}"