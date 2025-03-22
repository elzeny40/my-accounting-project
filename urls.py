from django.urls import path, include
from django.views.generic import TemplateView
from . import views, views_api, views_treasury, views_vehicle
from .views import (
    HomeView, UserListView, UserCreateView, UserUpdateView, UserDeleteView,
    ClientListView, ClientCreateView, ClientUpdateView, ClientDeleteView, ClientBalanceLogsView, ClientStatementView,
    DriverListView, DriverCreateView, DriverUpdateView, DriverDeleteView,
    OilTypeListView, OilTypeCreateView, OilTypeUpdateView, OilTypeDeleteView,
    PurchaseListView, PurchaseCreateView, PurchaseUpdateView, PurchaseDeleteView,
    SaleListView, SaleCreateView, SaleUpdateView, SaleDeleteView
)
from .views_vehicle import (
    VehicleMovementListView, VehicleMovementCreateView, VehicleMovementUpdateView,
    VehicleMovementDeleteView, VehicleMovementDetailView, vehicle_movement_export
)

urlpatterns = [
    # Base URLs
    path('', HomeView.as_view(), name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', UserCreateView.as_view(), name='register'),
    
    # User URLs
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    
    # Client URLs
    path('clients/', ClientListView.as_view(), name='client_list'),
    path('clients/create/', ClientCreateView.as_view(), name='client_create'),
    path('clients/<int:pk>/edit/', ClientUpdateView.as_view(), name='client_update'),
    path('clients/<int:pk>/delete/', ClientDeleteView.as_view(), name='client_delete'),
    path('clients/<int:pk>/balance-logs/', ClientBalanceLogsView.as_view(), name='client_balance_logs'),
    path('clients/statement/', ClientStatementView.as_view(), name='client_statement'),
    
    # Driver URLs
    path('drivers/', DriverListView.as_view(), name='driver_list'),
    path('drivers/create/', DriverCreateView.as_view(), name='driver_create'),
    path('drivers/<int:pk>/edit/', DriverUpdateView.as_view(), name='driver_update'),
    path('drivers/<int:pk>/delete/', DriverDeleteView.as_view(), name='driver_delete'),
    
    # Oil Type URLs
    path('oiltypes/', OilTypeListView.as_view(), name='oiltype_list'),
    path('oiltypes/create/', OilTypeCreateView.as_view(), name='oiltype_create'),
    path('oiltypes/<str:pk>/edit/', OilTypeUpdateView.as_view(), name='oiltype_update'),
    path('oiltypes/<str:pk>/delete/', OilTypeDeleteView.as_view(), name='oiltype_delete'),
    
    # Purchase URLs
    path('purchases/', PurchaseListView.as_view(), name='purchase_list'),
    path('purchases/create/', PurchaseCreateView.as_view(), name='purchase_create'),
    path('purchases/<int:pk>/edit/', PurchaseUpdateView.as_view(), name='purchase_update'),
    path('purchases/<int:pk>/delete/', PurchaseDeleteView.as_view(), name='purchase_delete'),
    
    # Sale URLs
    path('sales/', SaleListView.as_view(), name='sale_list'),
    path('sales/create/', SaleCreateView.as_view(), name='sale_create'),
    path('sales/<int:pk>/edit/', SaleUpdateView.as_view(), name='sale_update'),
    path('sales/<int:pk>/delete/', SaleDeleteView.as_view(), name='sale_delete'),
    
    # Vehicle Movement URLs
    path('vehicle-movements/', VehicleMovementListView.as_view(), name='vehicle_movement_list'),
    path('vehicle-movements/create/internal/', VehicleMovementCreateView.as_view(), {'movement_type': 'internal'}, name='vehicle_movement_create_internal'),
    path('vehicle-movements/create/external/', VehicleMovementCreateView.as_view(), {'movement_type': 'external'}, name='vehicle_movement_create_external'),
    path('vehicle-movements/<str:pk>/', VehicleMovementDetailView.as_view(), name='vehicle_movement_detail'),
    path('vehicle-movements/<str:pk>/edit/', VehicleMovementUpdateView.as_view(), name='vehicle_movement_update'),
    path('vehicle-movements/<str:pk>/delete/', VehicleMovementDeleteView.as_view(), name='vehicle_movement_delete'),
    path('vehicle-movements/export/', vehicle_movement_export, name='vehicle_movement_export'),
    
    # Treasury URLs
    path('treasury/', views_treasury.TreasuryListView.as_view(), name='treasury_list'),
    path('treasury/create/', views_treasury.TreasuryCreateView.as_view(), name='treasury_create'),
    path('treasury/<int:pk>/edit/', views_treasury.TreasuryUpdateView.as_view(), name='treasury_update'),
    path('treasury/<int:pk>/delete/', views_treasury.TreasuryDeleteView.as_view(), name='treasury_delete'),
    
    # API URLs
    path('api/operations/<str:operation_type>/list/', views_api.get_operations_list, name='api_operations_list'),
    path('api/operations/<str:operation_type>/<int:operation_id>/', views_api.get_operation_details, name='api_operation_details'),
    
    # Treasury API URLs
    path('api/sales/', views_treasury.get_sales_json, name='api_sales'),
    path('api/purchases/', views_treasury.get_purchases_json, name='api_purchases'),
    path('api/clients/', views_treasury.get_clients_json, name='api_clients'),
    path('api/drivers/', views_treasury.get_drivers_json, name='api_drivers'),
    path('api/sales/<int:sale_id>/', views_treasury.get_sale_by_id, name='api_sale_detail'),
    path('api/purchases/<int:purchase_id>/', views_treasury.get_purchase_by_id, name='api_purchase_detail'),
    
    # Vehicle Movement API URLs - Using views_vehicle for driver and freight endpoints
    path('api/drivers/<int:driver_id>/vehicle/', views_vehicle.get_driver_vehicle, name='get_driver_vehicle'),
    path('api/calculate-freight/', views_vehicle.calculate_freight, name='calculate_freight'),
]