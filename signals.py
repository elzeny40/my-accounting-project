from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models_vehicle import VehicleMovement
from .models import Sale, Purchase
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=VehicleMovement)
def validate_vehicle_movement(sender, instance, **kwargs):
    """التحقق من صحة بيانات حركة السيارة قبل الحفظ"""
    if instance.driver_freight and instance.client_freight:
        if instance.driver_freight > instance.client_freight:
            raise ValidationError({
                'driver_freight': 'نولون السائق لا يمكن أن يتجاوز نولون العميل',
                'client_freight': 'نولون العميل يجب أن يكون أكبر من أو يساوي نولون السائق'
            })

@receiver(post_save, sender=VehicleMovement)
def handle_vehicle_movement_save(sender, instance, created, **kwargs):
    """Update related sale/purchase when vehicle movement is saved"""
    if instance.movement_type == 'internal' and instance.operation_type and instance.operation_id:
        # Update related sale/purchase with movement details
        if instance.operation_type == 'sale':
            try:
                sale = Sale.objects.get(id=instance.operation_id)
                sale.driver = instance.driver
                sale.vehicle_number = instance.vehicle_number
                sale.loading_location = instance.loading_location
                sale.unloading_location = instance.unloading_location
                sale.driver_freight = instance.driver_freight
                sale.client_freight = instance.client_freight
                sale.save()
            except Sale.DoesNotExist:
                pass
        elif instance.operation_type == 'purchase':
            try:
                purchase = Purchase.objects.get(id=instance.operation_id)
                purchase.driver = instance.driver
                purchase.vehicle_number = instance.vehicle_number
                purchase.loading_location = instance.loading_location
                purchase.unloading_location = instance.unloading_location
                purchase.driver_freight = instance.driver_freight
                purchase.client_freight = instance.client_freight
                purchase.save()
            except Purchase.DoesNotExist:
                pass

@receiver([post_save], sender=Sale)
def handle_sale_save(sender, instance, created, **kwargs):
    """تحديث حركات السيارات المرتبطة بعملية البيع"""
    if instance.driver and instance.vehicle_number:
        try:
            movement = VehicleMovement.objects.get(
                movement_type='internal',
                operation_type='sale',
                operation_id=instance.id
            )
            # تحديث بيانات الحركة
            movement.driver = instance.driver
            movement.vehicle_number = instance.vehicle_number
            movement.loading_location = instance.loading_location
            movement.unloading_location = instance.unloading_location
            movement.driver_freight = instance.driver_freight
            movement.client_freight = instance.client_freight
            movement.save()
            logger.info(f"Updated vehicle movement for sale {instance.id}")
        except VehicleMovement.DoesNotExist:
            # إنشاء حركة جديدة
            VehicleMovement.objects.create(
                movement_type='internal',
                operation_type='sale',
                operation_id=instance.id,
                date=instance.date,
                client=instance.client,
                oil_type=instance.oil_type,
                quantity=instance.quantity,
                driver=instance.driver,
                vehicle_number=instance.vehicle_number,
                loading_location=instance.loading_location,
                unloading_location=instance.unloading_location,
                driver_freight=instance.driver_freight,
                client_freight=instance.client_freight
            )
            logger.info(f"Created new vehicle movement for sale {instance.id}")
        except Exception as e:
            logger.error(f"Error handling sale {instance.id}: {str(e)}")

@receiver([post_save], sender=Purchase)
def handle_purchase_save(sender, instance, created, **kwargs):
    """تحديث حركات السيارات المرتبطة بعملية الشراء"""
    if instance.driver and instance.vehicle_number:
        try:
            movement = VehicleMovement.objects.get(
                movement_type='internal',
                operation_type='purchase',
                operation_id=instance.id
            )
            # تحديث بيانات الحركة
            movement.driver = instance.driver
            movement.vehicle_number = instance.vehicle_number
            movement.loading_location = instance.loading_location
            movement.unloading_location = instance.unloading_location
            movement.driver_freight = instance.driver_freight
            movement.client_freight = instance.client_freight
            movement.save()
            logger.info(f"Updated vehicle movement for purchase {instance.id}")
        except VehicleMovement.DoesNotExist:
            # إنشاء حركة جديدة
            VehicleMovement.objects.create(
                movement_type='internal',
                operation_type='purchase',
                operation_id=instance.id,
                date=instance.date,
                client=instance.supplier,
                oil_type=instance.oil_type,
                quantity=instance.quantity,
                driver=instance.driver,
                vehicle_number=instance.vehicle_number,
                loading_location=instance.loading_location,
                unloading_location=instance.unloading_location,
                driver_freight=instance.driver_freight,
                client_freight=instance.client_freight
            )
            logger.info(f"Created new vehicle movement for purchase {instance.id}")
        except Exception as e:
            logger.error(f"Error handling purchase {instance.id}: {str(e)}")