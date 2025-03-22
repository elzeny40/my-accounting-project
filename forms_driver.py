from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Driver

class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['name', 'id_number', 'address', 'phone_number', 'license_number', 'license_type', 'license_expiry_date', 'vehicle_number', 'vehicle_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'license_type': forms.Select(attrs={'class': 'form-control'}),
            'license_expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_type': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            return phone_number  # السماح بأن يكون رقم الهاتف فارغًا
        
        # إزالة المسافات والرموز غير المرغوب فيها
        phone_number = ''.join(c for c in phone_number if c.isdigit())
        
        # التحقق من صحة الرقم
        if not phone_number.startswith('01'):
            raise ValidationError('رقم الهاتف يجب أن يبدأ بـ 01')
        if len(phone_number) != 11:
            raise ValidationError('رقم الهاتف يجب أن يتكون من 11 رقم')
            
        return phone_number
        
    def clean(self):
        cleaned_data = super().clean()
        # التحقق من تاريخ انتهاء الرخصة
        license_expiry_date = cleaned_data.get('license_expiry_date')
        if license_expiry_date and license_expiry_date < timezone.now().date():
            self.add_error('license_expiry_date', 'تاريخ انتهاء الرخصة يجب أن يكون في المستقبل')
            
        # التحقق من رقم السيارة
        vehicle_number = cleaned_data.get('vehicle_number')
        if not vehicle_number:
            self.add_error('vehicle_number', 'يجب إدخال رقم السيارة')
            
        return cleaned_data