from django.utils import timezone
from django.urls import resolve
from django.core.cache import cache
from django.conf import settings
from django.urls.exceptions import Resolver404
from django.db import transaction
from .models_vehicle import VehicleMovement

class ActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.cache_timeout = getattr(settings, 'ACTIVITY_LOG_CACHE_TIMEOUT', 300)  # 5 minutes default

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            try:
                # Use caching to reduce database queries
                cache_key = f'activity_log_{request.user.id}_{request.path}'
                if not cache.get(cache_key):
                    from .models import ActivityLog
                    
                    try:
                        url_name = resolve(request.path).url_name or request.path
                    except Resolver404:
                        url_name = request.path

                    # Filter sensitive headers
                    safe_headers = {k: v for k, v in request.headers.items() 
                                  if k.lower() not in ['cookie', 'authorization', 'session']}
                    
                    # Batch create activity logs
                    ActivityLog.objects.create(
                        user=request.user,
                        action=f"Accessed {url_name} via {request.method}",
                        details=str(safe_headers),
                        timestamp=timezone.now()
                    )
                    
                    # Set cache to prevent duplicate logs
                    cache.set(cache_key, True, self.cache_timeout)
            except Exception as e:
                # Log the error but don't break the request-response cycle
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Activity logging failed: {str(e)}')

        return response

class VehicleMovementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Process view is called just before Django calls the view"""
        # Only process vehicle movement creation views
        if hasattr(view_func, 'view_class') and view_func.view_class.__name__ == 'VehicleMovementCreateView':
            movement_type = view_kwargs.get('movement_type', 'external')
            
            # Get next available ID
            with transaction.atomic():
                prefix = 'VEi-' if movement_type == 'internal' else 'VEe-'
                last_movement = VehicleMovement.objects.select_for_update().filter(
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
                
                request.next_movement_id = f'{prefix}{next_number:03d}'
        
        return None