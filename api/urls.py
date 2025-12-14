from rest_framework.routers import DefaultRouter
from django.urls import path, include

# 1. UPDATED: Import the CustomObtainAuthToken view
from .views import (
    # Core Entities
    UserViewSet, 
    CompanyViewSet, 
    StationViewSet, 
    PumpViewSet,
    InventoryViewSet, 
    
    # Transactions (Split into List/Create)
    TransactionListViewSet, 
    TransactionCreateAPIView,
    
    # Alerts and Settings
    AlertViewSet,
    # SystemSettingViewSet 

    # --- ADDED: The Custom Token View ---
    CustomObtainAuthToken,
)

router = DefaultRouter()

# 1. Core CRUD and Management Endpoints (Handled by the Router)
# URL Pattern: /api/v1/{resource}/
router.register(r'users', UserViewSet, basename='user')
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'stations', StationViewSet, basename='station')
router.register(r'pumps', PumpViewSet, basename='pump')
router.register(r'inventory', InventoryViewSet, basename='inventory') # Read/Controlled Update
router.register(r'alerts', AlertViewSet, basename='alert')             # Read/Controlled Update (Status)

# 2. Transaction List/Detail/Filter (Read-only)
router.register(r'transactions', TransactionListViewSet, basename='transaction')

# 3. System Settings (Pricing) Management
# router.register(r'settings', SystemSettingViewSet, basename='setting')


urlpatterns = [
    # Router paths (e.g., /api/v1/users, /api/v1/stations, /api/v1/transactions)
    path('', include(router.urls)),

    # Custom Endpoint: Transaction Creation (High-traffic, complex business logic)
    path(
        'transactions/create/',
        TransactionCreateAPIView.as_view({'post': 'create'}),
        name='transaction-create'
    ),
    
    # --- ADDED: Custom Token Authentication URL ---
    # This path is now handled by your custom view which uses the 'email' field for login.
    path(
        'auth/token/', 
        CustomObtainAuthToken.as_view(), 
        name='api-token-auth'
    ),

    # NOTE: The default path below is REMOVED to prevent the CSRF error.
    # path('auth/', include('rest_framework.urls', namespace='rest_framework')), 
    # Use the /auth/token/ endpoint above instead of the session login views.
]