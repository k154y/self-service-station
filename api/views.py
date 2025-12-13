# C:\Users\k.yves\Desktop\self_service_station\api\views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from rest_framework.decorators import action
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from service.models import User, Company, Station, Pump, Inventory, Transaction, Alert
# Assuming get_user_stations helper is in service.views
from service.views import get_user_stations 
from .serializers import (
    UserSerializer, UserCreateSerializer, CompanySerializer, StationSerializer, 
    PumpSerializer, InventorySerializer, TransactionSerializer, 
    TransactionCreateSerializer, AlertSerializer
)

# --- Custom Permissions Class (Completed) ---

class HasCompanyAccess(BasePermission):
    """
    Custom permission to only allow access to resources the user is authorized for.
    Based on the logic in the original HasCompanyAccess snippet.
    """
    def has_permission(self, request, view):
        # Must be logged in via session
        return bool(request.session.get('user_id'))

    def has_object_permission(self, request, view, obj):
        user_role = request.session.get('role')
        user_id = request.session.get('user_id')
        
        if user_role == 'admin':
            return True
        
        # --- Owner Logic ---
        if user_role == 'owner':
            try:
                if isinstance(obj, Company):
                    company = obj
                elif isinstance(obj, Station):
                    company = obj.company_id
                elif hasattr(obj, 'station') and obj.station: # Pump, Alert
                    company = obj.station.company_id
                elif hasattr(obj, 'station_id') and obj.station_id: # Inventory, Transaction
                    company = obj.station_id.company_id
                else:
                    return False
                return company.owner.user_id == user_id
            except Exception:
                return False
        
        # --- Manager Logic ---
        if user_role == 'manager':
            try:
                # Manager checks against station.manager_id == user_id
                if isinstance(obj, Station):
                    return obj.manager_id and obj.manager_id.user_id == user_id
                
                # Check for objects linked to a station (Pump, Alert, Inventory, Transaction)
                # Note: Assuming Pump, Alert use 'station', Inventory, Transaction use 'station_id'
                if (hasattr(obj, 'station') and obj.station and 
                    obj.station.manager_id and obj.station.manager_id.user_id == user_id):
                    return True
                
                if (hasattr(obj, 'station_id') and obj.station_id and 
                    obj.station_id.manager_id and obj.station_id.manager_id.user_id == user_id):
                    return True
                
                return False
            except Exception:
                return False
        
        return False


# --- User API ---
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [HasCompanyAccess]
    
    def get_queryset(self):
        user_role = self.request.session.get('role')
        user_id = self.request.session.get('user_id')
        
        if user_role == 'admin':
            return User.objects.all().order_by('user_id')
        
        if user_role == 'owner':
            # Owner sees themselves and managers under their company
            my_companies = Company.objects.filter(owner__user_id=user_id)
            # Managers associated with those companies' stations
            manager_ids = Station.objects.filter(company_id__in=my_companies).values_list('manager_id', flat=True)
            # Filter users: owner's managers + the owner themselves
            return User.objects.filter(Q(user_id__in=manager_ids) | Q(user_id=user_id)).order_by('user_id')
            
        if user_role == 'manager':
            # Manager sees only themselves
            return User.objects.filter(user_id=user_id).order_by('user_id')

        return User.objects.none()

    def get_serializer_class(self):
        # Use a serializer that allows password hashing on create/update
        if self.action in ['create', 'update', 'partial_update']:
            return UserCreateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        user_role = request.session.get('role')
        if user_role not in ['admin', 'owner']:
            return Response({'detail': 'You are not allowed to create users.'}, status=status.HTTP_403_FORBIDDEN)
        
        if user_role == 'owner' and request.data.get('role') != 'manager':
            return Response({'detail': 'Owners can only create Managers.'}, status=status.HTTP_403_FORBIDDEN)

        # Use the custom serializer for validation and creation
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # Note: Default update/delete is allowed for Admin and Owner (via HasCompanyAccess)


# --- Company API ---
class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [HasCompanyAccess]
    
    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        
        if user_role == 'admin':
            return Company.objects.all()
        
        if user_role == 'owner':
            # Owner sees only companies they own
            return Company.objects.filter(owner__user_id=user_id)
            
        return Company.objects.none()
        
    # Note: Manager has no read/write access to Company objects by default (returns none).


# --- Station API ---
class StationViewSet(viewsets.ModelViewSet):
    serializer_class = StationSerializer
    permission_classes = [HasCompanyAccess]
    
    def get_queryset(self):
        # Uses the helper function to filter stations by user role/access
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        return get_user_stations(user_id, user_role)

    def perform_validation_and_save(self, serializer, instance=None):
        """Helper to enforce the Manager-per-Company rule on create and update."""
        manager_id = serializer.validated_data.get('manager_id')
        company_id = serializer.validated_data.get('company_id')

        if manager_id and manager_id.role == 'manager':
            # Find stations this manager already manages, excluding the current station if updating
            exclude_pk = instance.pk if instance else None
            existing_stations = Station.objects.filter(manager_id=manager_id).exclude(pk=exclude_pk)
            
            if existing_stations.exists():
                existing_company = existing_stations.first().company_id
                if existing_company != company_id:
                    raise serializers.ValidationError(
                        f'Manager {manager_id.username} already manages a station for company "{existing_company.name}". They cannot be assigned to a station under "{company_id.name}".'
                    )
        
        if instance:
            serializer.save()
        else:
            self.perform_create(serializer)


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            self.perform_validation_and_save(serializer)
        except serializers.ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_validation_and_save(serializer, instance=instance)
        except serializers.ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data)


# --- Pump API ---
class PumpViewSet(viewsets.ModelViewSet):
    serializer_class = PumpSerializer
    permission_classes = [HasCompanyAccess]
    
    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        stations = get_user_stations(user_id, user_role)
        return Pump.objects.filter(station__in=stations).order_by('station__name', 'pump_number')
        
    @action(detail=True, methods=['patch'], url_path='status-update')
    def status_update(self, request, pk=None):
        """Allows quick update of pump status (Active/Offline)."""
        pump = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status or new_status not in [choice[0] for choice in Pump.STATUS_CHOICES]:
            return Response({'detail': 'Invalid or missing status value.'}, status=status.HTTP_400_BAD_REQUEST)

        # Re-run object permission check just in case
        if not self.has_object_permission(request, self, pump):
            return Response({'detail': 'You do not have permission to update this pump.'}, status=status.HTTP_403_FORBIDDEN)

        pump.status = new_status
        pump.save()
        
        return Response(self.get_serializer(pump).data, status=status.HTTP_200_OK)


# --- Inventory API ---
# Note: This is based on the logic developed in the previous step
class InventoryViewSet(viewsets.ModelViewSet):
    serializer_class = InventorySerializer
    permission_classes = [HasCompanyAccess]
    
    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        stations = get_user_stations(user_id, user_role)
        return Inventory.objects.filter(station_id__in=stations)

    def create(self, request, *args, **kwargs):
        """Prevents creation via API."""
        return Response(
            {'detail': 'Inventory items must be initialized internally. Creation via API is forbidden.'}, 
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def destroy(self, request, *args, **kwargs):
        """Prevents deletion via API."""
        return Response(
            {'detail': 'Inventory records cannot be deleted.'}, 
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def update(self, request, *args, **kwargs):
        # Enforce role-based update logic (Owners/Admins only)
        
        if self.request.session.get('role') == 'manager':
            return Response({'detail': 'Managers cannot update inventory prices/levels via API.'}, 
                            status=status.HTTP_403_FORBIDDEN)
                            
        instance = self.get_object()
        data = {
            # Only allow update for these specific fields, matching InventoryUpdateForm
            'quantity': request.data.get('quantity'),
            'unit_price': request.data.get('unit_price'),
            'min_threshold': request.data.get('min_threshold')
        }
        
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


# --- Transaction API ---
# Read-only ViewSet for list and filter functionality
class TransactionListViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [HasCompanyAccess]

    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        
        authorized_stations = get_user_stations(user_id, user_role)
        queryset = Transaction.objects.filter(station_id__in=authorized_stations)
        
        # Implement Filtering/Searching logic from TransactionListView
        
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(fuel_type__icontains=search_query) | 
                Q(payment_method__icontains=search_query) | 
                Q(car_plate__icontains=search_query) | 
                Q(transaction_id__icontains=search_query)
            )

        duration = self.request.query_params.get('duration', 'all')
        if duration != 'all':
            time_ago = timezone.now()
            if duration == '24hrs':
                time_ago -= timedelta(hours=24)
            elif duration == 'week':
                time_ago -= timedelta(weeks=1)
            elif duration == 'month':
                time_ago -= timedelta(days=30)
            queryset = queryset.filter(transaction_time__gte=time_ago)

        payment_method = self.request.query_params.get('payment_method', 'all')
        if payment_method != 'all':
            queryset = queryset.filter(payment_method=payment_method)
            
        station_id = self.request.query_params.get('station_id', 'all')
        if station_id != 'all' and station_id.isdigit():
            # Only allow filtering within authorized stations (already handled by base query)
            queryset = queryset.filter(station_id=station_id)

        # Default ordering: most recent first
        return queryset.order_by('-transaction_time')

# Creation ViewSet (used for the /transactions/create/ endpoint)
class TransactionCreateAPIView(viewsets.GenericViewSet, viewsets.mixins.CreateModelMixin):
    serializer_class = TransactionCreateSerializer
    permission_classes = [HasCompanyAccess] 
    
    def perform_create(self, serializer):
        # NOTE: This is where you would integrate the complex logic from 
        # TransactionCreateView in service.views, which likely handles:
        # 1. Validation of business logic (e.g., fuel type matches pump/inventory)
        # 2. Atomicity (using @transaction.atomic)
        # 3. Inventory deduction
        # 4. Alert generation (if inventory drops below threshold)
        
        # For simplicity, we only perform the save here.
        serializer.save() 
        

# --- Alert API ---
# Note: This is based on the logic developed in the previous step
class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [HasCompanyAccess]
    http_method_names = ['get', 'patch', 'head', 'options'] # Restrict to Read and Status Update
    
    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        user_role = self.request.session.get('role')
        stations = get_user_stations(user_id, user_role)
        # Filter alerts belonging to those stations and default to pending
        status_filter = self.request.query_params.get('status', None)
        queryset = Alert.objects.filter(station__in=stations).order_by('-created_at')
        
        if status_filter in [choice[0] for choice in Alert.status_choices]:
            queryset = queryset.filter(status=status_filter)
        
        return queryset

    def update(self, request, *args, **kwargs):
        # Only allow partial update and only for the 'status' field
        instance = self.get_object()
        
        if len(request.data) != 1 or 'status' not in request.data:
            return Response({'detail': 'Only the "status" field can be updated.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Use partial=True to update only the status field
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)