from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models_vehicle import VehicleMovement
from .models import Sale, Purchase, Client, Driver, OilType

class VehicleMovementForm(forms.ModelForm):
    class Meta:
        model = VehicleMovement
        fields = ['movement_type', 'operation_type', 'operation_id', 'date', 'client', 'oil_type', 'quantity',
                'driver', 'vehicle_number', 'loading_location', 'unloading_location',
                'driver_freight', 'client_freight']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'client': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'اختر العميل'
            }),
            'oil_type': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'اختر نوع الزيت'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'driver': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'اختر السائق'
            }),
            'vehicle_number': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            'loading_location': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'unloading_location': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'driver_freight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'client_freight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'movement_type': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        driver_freight = cleaned_data.get('driver_freight')
        client_freight = cleaned_data.get('client_freight')
        quantity = cleaned_data.get('quantity')

        if quantity is not None and quantity <= 0:
            raise ValidationError({
                'quantity': 'الكمية يجب أن تكون أكبر من صفر'
            })

        if driver_freight and client_freight:
            if driver_freight > client_freight:
                raise ValidationError({
                    'driver_freight': 'نولون السائق لا يمكن أن يتجاوز نولون العميل',
                    'client_freight': 'نولون العميل يجب أن يكون أكبر من أو يساوي نولون السائق'
                })
        
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicle_number'].required = True
        self.fields['loading_location'].required = True
        self.fields['unloading_location'].required = True
        
        # إضافة تلميحات للمستخدم
        self.fields['quantity'].help_text = 'أدخل الكمية بالطن (حتى 3 أرقام عشرية)'
        self.fields['driver_freight'].help_text = 'نولون السائق يجب أن يكون أقل من أو يساوي نولون العميل'
        self.fields['client_freight'].help_text = 'نولون العميل يجب أن يكون أكبر من أو يساوي نولون السائق'

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
        return instance

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المستخدم'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'كلمة المرور'})
    )

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['date', 'supplier', 'oil_type', 'quantity', 'price', 'loading_location', 
                 'unloading_location', 'driver', 'vehicle_number', 'driver_freight', 
                 'client_freight', 'description']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'supplier': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'اختر المورد',
                'required': False
            }),
            'oil_type': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'اختر نوع الزيت'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'loading_location': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'unloading_location': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'driver': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'اختر السائق'
            }),
            'vehicle_number': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'driver_freight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'client_freight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        driver_freight = cleaned_data.get('driver_freight')
        client_freight = cleaned_data.get('client_freight')
        quantity = cleaned_data.get('quantity')

        if quantity is not None and quantity <= 0:
            raise ValidationError({
                'quantity': 'الكمية يجب أن تكون أكبر من صفر'
            })

        if driver_freight and client_freight:
            if driver_freight > client_freight:
                raise ValidationError({
                    'driver_freight': 'نولون السائق لا يمكن أن يتجاوز نولون العميل',
                    'client_freight': 'نولون العميل يجب أن يكون أكبر من أو يساوي نولون السائق'
                })
        
        return cleaned_data