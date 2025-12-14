from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    # Authentication (function-based)
    path('', views.landing_page, name='landing_page'),
    path('signup/', views.signup_page, name='signup'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.user_logout, name='logout'),
    
    # User CRUD (class-based)
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:user_id>/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:user_id>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    
    # Company CRUD
    path('companies/', views.CompanyListView.as_view(), name='company_list'),
    path('companies/create/', views.CompanyCreateView.as_view(), name='company_create'),
    path('companies/<int:company_id>/update/', views.CompanyUpdateView.as_view(), name='company_update'),
    path('companies/<int:company_id>/delete/', views.CompanyDeleteView.as_view(), name='company_delete'),
    
    # Station CRUD
    path('stations/', views.StationListView.as_view(), name='station_list'),
    path('stations/create/', views.StationCreateView.as_view(), name='station_create'),
    path('stations/<int:station_id>/update/', views.StationUpdateView.as_view(), name='station_update'),
    path('stations/<int:station_id>/delete/', views.StationDeleteView.as_view(), name='station_delete'),
    
    # Pump CRUD
    path('pumps/', views.PumpListView.as_view(), name='pump_list'),
    path('admin-tools/pumps/', views.AdminPumpListView.as_view(), name='admin_pump_list'),
    path('pumps/create/', views.PumpCreateView.as_view(), name='pump_create'),
    path('pumps/<int:pump_id>/update/', views.PumpUpdateView.as_view(), name='pump_update'),
    path('pumps/<int:pump_id>/status/', views.pump_status_update, name='pump_status_update'),
    path('pumps/<int:pump_id>/delete/', views.PumpDeleteView.as_view(), name='pump_delete'),
    
    # Inventory CRUD
    path('inventory/', views.InventoryListView.as_view(), name='inventory_list'),
    path('inventory/<int:inventory_id>/update/', views.InventoryUpdateView.as_view(), name='inventory_update'),
    
    # Transaction CRUD
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/create/', views.TransactionCreateView.as_view(), name='transaction_create'),
    
    # Alert CRUD
    path('alerts/', views.AlertListView.as_view(), name='alert_list'),
    path('alerts/<int:alert_id>/update/', views.AlertUpdateView.as_view(), name='alert_update'),
    
    # Settings CRUD
    path('settings/', views.SystemSettingListView.as_view(), name='settings_list'),
    path('settings/create/', views.SystemSettingCreateView.as_view(), name='settings_create'),
    path('settings/<int:setting_id>/update/', views.SystemSettingUpdateView.as_view(), name='settings_update'),
    path('settings/<int:setting_id>/delete/', views.SystemSettingDeleteView.as_view(), name='settings_delete'),
]