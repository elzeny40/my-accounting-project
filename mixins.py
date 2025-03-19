from django.core.exceptions import PermissionDenied

class AdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

class RoleRequiredMixin:
    """A mixin that allows specific roles to access a view"""
    required_roles = ['admin']
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in self.required_roles:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

class ClientManagerRequiredMixin(RoleRequiredMixin):
    required_roles = ['admin', 'client_manager']

class VehicleManagerRequiredMixin(RoleRequiredMixin):
    required_roles = ['admin', 'vehicle_manager']

class TransactionManagerRequiredMixin(RoleRequiredMixin):
    required_roles = ['admin', 'transaction_manager']