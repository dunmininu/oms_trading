"""
OMS services for order management, executions, positions, and P&L.
"""

from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from django.db.models import Q, Sum, F
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
import uuid

from apps.core.models import User
from apps.tenants.models import Tenant
from apps.brokers.models import BrokerAccount
from .models import Order, Execution, Position, PnLSnapshot, Instrument


class OrderService:
    """Service for order management operations."""
    
    def __init__(self, tenant: Tenant, user: User):
        self.tenant = tenant
        self.user = user
    
    def create_order(self, order_data: Dict[str, Any]) -> Order:
        """Create a new order with validation."""
        with transaction.atomic():
            # Validate instrument exists and is tradable
            instrument = Instrument.objects.get(
                id=order_data['instrument_id'],
                is_active=True,
                is_tradable=True
            )
            
            # Validate broker account belongs to tenant
            broker_account = BrokerAccount.objects.get(
                id=order_data['broker_account_id'],
                tenant=self.tenant,
                is_active=True
            )
            
            # Generate unique client order ID if not provided
            if 'client_order_id' not in order_data:
                order_data['client_order_id'] = f"{self.tenant.subdomain}_{uuid.uuid4().hex[:8]}"
            
            # Create order
            order = Order.objects.create(
                tenant=self.tenant,
                user=self.user,
                broker_account=broker_account,
                instrument=instrument,
                **order_data
            )
            
            return order
    
    def get_order(self, order_id: str) -> Order:
        """Get order by ID with tenant scoping."""
        return Order.objects.get(
            id=order_id,
            tenant=self.tenant
        )
    
    def list_orders(
        self, 
        filters: Dict[str, Any] = None, 
        limit: int = 100, 
        offset: int = 0
    ) -> Tuple[List[Order], int, bool]:
        """List orders with filtering and pagination."""
        queryset = Order.objects.filter(tenant=self.tenant)
        
        if filters:
            if filters.get('instrument_symbol'):
                queryset = queryset.filter(instrument__symbol__icontains=filters['instrument_symbol'])
            
            if filters.get('broker_account_id'):
                queryset = queryset.filter(broker_account_id=filters['broker_account_id'])
            
            if filters.get('order_type'):
                queryset = queryset.filter(order_type=filters['order_type'])
            
            if filters.get('side'):
                queryset = queryset.filter(side=filters['side'])
            
            if filters.get('state'):
                queryset = queryset.filter(state=filters['state'])
            
            if filters.get('user_id'):
                queryset = queryset.filter(user_id=filters['user_id'])
            
            if filters.get('strategy_run_id'):
                queryset = queryset.filter(strategy_run_id=filters['strategy_run_id'])
            
            if filters.get('date_from'):
                queryset = queryset.filter(created_at__gte=filters['date_from'])
            
            if filters.get('date_to'):
                queryset = queryset.filter(created_at__lte=filters['date_to'])
        
        # Order by most recent first
        queryset = queryset.order_by('-created_at')
        
        total_count = queryset.count()
        orders = list(queryset[offset:offset + limit + 1])
        has_next = len(orders) > limit
        
        if has_next:
            orders = orders[:-1]
        
        return orders, total_count, has_next
    
    def update_order(self, order_id: str, update_data: Dict[str, Any]) -> Order:
        """Update order with optimistic concurrency control."""
        with transaction.atomic():
            order = self.get_order(order_id)
            
            # Check if order can be modified
            if not order.is_active:
                raise ValidationError("Order cannot be modified in its current state")
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(order, field) and field not in ['id', 'tenant', 'user']:
                    setattr(order, field, value)
            
            order.save()
            return order
    
    def cancel_order(self, order_id: str) -> Order:
        """Cancel an order."""
        with transaction.atomic():
            order = self.get_order(order_id)
            
            if not order.is_active:
                raise ValidationError("Order cannot be cancelled in its current state")
            
            order.state = 'CANCELLED'
            order.cancelled_at = timezone.now()
            order.save()
            
            return order
    
    def create_bulk_orders(self, orders_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple orders in a single transaction."""
        with transaction.atomic():
            created_orders = []
            errors = []
            
            for i, order_data in enumerate(orders_data):
                try:
                    order = self.create_order(order_data)
                    created_orders.append(order)
                except Exception as e:
                    errors.append({
                        'index': i,
                        'error': str(e),
                        'data': order_data
                    })
            
            return {
                'created_orders': created_orders,
                'errors': errors,
                'success_count': len(created_orders),
                'error_count': len(errors)
            }
    
    def cancel_bulk_orders(self, order_ids: List[str]) -> Dict[str, Any]:
        """Cancel multiple orders in a single transaction."""
        with transaction.atomic():
            cancelled_orders = []
            errors = []
            
            for order_id in order_ids:
                try:
                    order = self.cancel_order(order_id)
                    cancelled_orders.append(order)
                except Exception as e:
                    errors.append({
                        'order_id': order_id,
                        'error': str(e)
                    })
            
            return {
                'cancelled_orders': cancelled_orders,
                'errors': errors,
                'success_count': len(cancelled_orders),
                'error_count': len(errors)
            }


class ExecutionService:
    """Service for execution management operations."""
    
    def __init__(self, tenant: Tenant, user: User):
        self.tenant = tenant
        self.user = user
    
    def get_execution(self, execution_id: str) -> Execution:
        """Get execution by ID with tenant scoping."""
        return Execution.objects.get(
            id=execution_id,
            tenant=self.tenant
        )
    
    def list_executions(
        self, 
        filters: Dict[str, Any] = None, 
        limit: int = 100, 
        offset: int = 0
    ) -> Tuple[List[Execution], int, bool]:
        """List executions with filtering and pagination."""
        queryset = Execution.objects.filter(tenant=self.tenant)
        
        if filters:
            if filters.get('order_id'):
                queryset = queryset.filter(order_id=filters['order_id'])
            
            if filters.get('instrument_symbol'):
                queryset = queryset.filter(order__instrument__symbol__icontains=filters['instrument_symbol'])
            
            if filters.get('broker_account_id'):
                queryset = queryset.filter(order__broker_account_id=filters['broker_account_id'])
            
            if filters.get('date_from'):
                queryset = queryset.filter(executed_at__gte=filters['date_from'])
            
            if filters.get('date_to'):
                queryset = queryset.filter(executed_at__lte=filters['date_to'])
        
        # Order by most recent first
        queryset = queryset.order_by('-executed_at')
        
        total_count = queryset.count()
        executions = list(queryset[offset:offset + limit + 1])
        has_next = len(executions) > limit
        
        if has_next:
            executions = executions[:-1]
        
        return executions, total_count, has_next
    
    def create_execution(self, execution_data: Dict[str, Any]) -> Execution:
        """Create a new execution record."""
        with transaction.atomic():
            # Validate order exists and belongs to tenant
            order = Order.objects.get(
                id=execution_data['order_id'],
                tenant=self.tenant
            )
            
            # Create execution
            execution = Execution.objects.create(
                tenant=self.tenant,
                order=order,
                **execution_data
            )
            
            # Update order state if needed
            self._update_order_state(order, execution)
            
            return execution
    
    def _update_order_state(self, order: Order, execution: Execution):
        """Update order state based on execution."""
        total_executed = order.executions.aggregate(
            total=Sum('quantity')
        )['total'] or Decimal('0')
        
        if total_executed >= order.quantity:
            order.state = 'FILLED'
            order.filled_at = timezone.now()
        elif total_executed > 0:
            order.state = 'PARTIALLY_FILLED'
        
        order.filled_quantity = total_executed
        
        # Calculate average price
        avg_price = order.executions.aggregate(
            avg_price=Sum(F('price') * F('quantity')) / Sum('quantity')
        )['avg_price']
        
        if avg_price:
            order.average_price = avg_price
        
        order.save()


class PositionService:
    """Service for position management operations."""
    
    def __init__(self, tenant: Tenant, user: User):
        self.tenant = tenant
        self.user = user
    
    def get_position(self, position_id: str) -> Position:
        """Get position by ID with tenant scoping."""
        return Position.objects.get(
            id=position_id,
            tenant=self.tenant
        )
    
    def list_positions(
        self, 
        filters: Dict[str, Any] = None, 
        limit: int = 100, 
        offset: int = 0
    ) -> Tuple[List[Position], int, bool]:
        """List positions with filtering and pagination."""
        queryset = Position.objects.filter(tenant=self.tenant)
        
        if filters:
            if filters.get('instrument_symbol'):
                queryset = queryset.filter(instrument__symbol__icontains=filters['instrument_symbol'])
            
            if filters.get('broker_account_id'):
                queryset = queryset.filter(broker_account_id=filters['broker_account_id'])
            
            if filters.get('has_position'):
                if filters['has_position']:
                    queryset = queryset.exclude(quantity=0)
                else:
                    queryset = queryset.filter(quantity=0)
        
        # Order by most recent first
        queryset = queryset.order_by('-last_updated')
        
        total_count = queryset.count()
        positions = list(queryset[offset:offset + limit + 1])
        has_next = len(positions) > limit
        
        if has_next:
            positions = positions[:-1]
        
        return positions, total_count, has_next
    
    def update_position(
        self, 
        broker_account: BrokerAccount, 
        instrument: Instrument, 
        quantity_change: Decimal, 
        price: Decimal,
        execution_time: timezone.datetime
    ) -> Position:
        """Update position based on execution."""
        with transaction.atomic():
            position, created = Position.objects.get_or_create(
                tenant=self.tenant,
                broker_account=broker_account,
                instrument=instrument,
                defaults={
                    'quantity': Decimal('0'),
                    'average_cost': Decimal('0'),
                    'unrealized_pnl': Decimal('0'),
                    'realized_pnl': Decimal('0')
                }
            )
            
            if created:
                position.quantity = quantity_change
                position.average_cost = price
            else:
                # Update position based on execution
                old_quantity = position.quantity
                old_avg_cost = position.average_cost
                
                new_quantity = old_quantity + quantity_change
                
                if new_quantity == 0:
                    # Position closed
                    if old_quantity > 0:  # Was long
                        realized_pnl = (price - old_avg_cost) * abs(quantity_change)
                    else:  # Was short
                        realized_pnl = (old_avg_cost - price) * abs(quantity_change)
                    
                    position.realized_pnl += realized_pnl
                    position.quantity = Decimal('0')
                    position.average_cost = Decimal('0')
                else:
                    # Position modified
                    if (old_quantity > 0 and quantity_change > 0) or (old_quantity < 0 and quantity_change < 0):
                        # Adding to position
                        total_cost = (old_quantity * old_avg_cost) + (quantity_change * price)
                        position.average_cost = total_cost / new_quantity
                    else:
                        # Reducing position
                        if old_quantity > 0:  # Was long
                            realized_pnl = (price - old_avg_cost) * abs(quantity_change)
                        else:  # Was short
                            realized_pnl = (old_avg_cost - price) * abs(quantity_change)
                        
                        position.realized_pnl += realized_pnl
                    
                    position.quantity = new_quantity
                
                position.last_updated = execution_time
                position.save()
            
            return position
    
    def get_position_summary(self, broker_account_id: str = None) -> Dict[str, Any]:
        """Get position summary for tenant or specific broker account."""
        queryset = Position.objects.filter(tenant=self.tenant)
        
        if broker_account_id:
            queryset = queryset.filter(broker_account_id=broker_account_id)
        
        summary = queryset.aggregate(
            total_positions=Sum('quantity'),
            total_market_value=Sum(F('quantity') * F('market_price')),
            total_cost_basis=Sum(F('quantity') * F('average_cost')),
            total_unrealized_pnl=Sum('unrealized_pnl'),
            total_realized_pnl=Sum('realized_pnl')
        )
        
        return {
            'total_positions': summary['total_positions'] or 0,
            'total_market_value': summary['total_market_value'] or Decimal('0'),
            'total_cost_basis': summary['total_cost_basis'] or Decimal('0'),
            'total_unrealized_pnl': summary['total_unrealized_pnl'] or Decimal('0'),
            'total_realized_pnl': summary['total_realized_pnl'] or Decimal('0'),
            'net_pnl': (summary['total_unrealized_pnl'] or Decimal('0')) + (summary['total_realized_pnl'] or Decimal('0'))
        }


class PnLService:
    """Service for P&L management operations."""
    
    def __init__(self, tenant: Tenant, user: User):
        self.tenant = tenant
        self.user = user
    
    def get_pnl_snapshot(self, snapshot_id: str) -> PnLSnapshot:
        """Get P&L snapshot by ID with tenant scoping."""
        return PnLSnapshot.objects.get(
            id=snapshot_id,
            tenant=self.tenant
        )
    
    def list_pnl_snapshots(
        self, 
        filters: Dict[str, Any] = None, 
        limit: int = 100, 
        offset: int = 0
    ) -> Tuple[List[PnLSnapshot], int, bool]:
        """List P&L snapshots with filtering and pagination."""
        queryset = PnLSnapshot.objects.filter(tenant=self.tenant)
        
        if filters:
            if filters.get('broker_account_id'):
                queryset = queryset.filter(broker_account_id=filters['broker_account_id'])
            
            if filters.get('date_from'):
                queryset = queryset.filter(snapshot_date__gte=filters['date_from'])
            
            if filters.get('date_to'):
                queryset = queryset.filter(snapshot_date__lte=filters['date_to'])
        
        # Order by most recent first
        queryset = queryset.order_by('-snapshot_date')
        
        total_count = queryset.count()
        snapshots = list(queryset[offset:offset + limit + 1])
        has_next = len(snapshots) > limit
        
        if has_next:
            snapshots = snapshots[:-1]
        
        return snapshots, total_count, has_next
    
    def create_pnl_snapshot(self, broker_account_id: str = None, snapshot_date: str = None) -> PnLSnapshot:
        """Create a new P&L snapshot."""
        with transaction.atomic():
            if not snapshot_date:
                snapshot_date = timezone.now().date()
            else:
                snapshot_date = timezone.datetime.strptime(snapshot_date, '%Y-%m-%d').date()
            
            # Get positions for snapshot
            position_service = PositionService(self.tenant, self.user)
            
            if broker_account_id:
                broker_accounts = [BrokerAccount.objects.get(id=broker_account_id, tenant=self.tenant)]
            else:
                broker_accounts = BrokerAccount.objects.filter(tenant=self.tenant, is_active=True)
            
            snapshots = []
            
            for broker_account in broker_accounts:
                # Get position summary
                position_summary = position_service.get_position_summary(str(broker_account.id))
                
                # Get detailed positions
                positions = Position.objects.filter(
                    tenant=self.tenant,
                    broker_account=broker_account
                ).exclude(quantity=0)
                
                positions_data = []
                for position in positions:
                    positions_data.append({
                        'instrument_symbol': position.instrument.symbol,
                        'quantity': float(position.quantity),
                        'average_cost': float(position.average_cost),
                        'market_price': float(position.market_price) if position.market_price else 0,
                        'market_value': float(position.market_value) if position.market_value else 0,
                        'unrealized_pnl': float(position.unrealized_pnl),
                        'realized_pnl': float(position.realized_pnl)
                    })
                
                # Create snapshot
                snapshot = PnLSnapshot.objects.create(
                    tenant=self.tenant,
                    broker_account=broker_account,
                    snapshot_date=snapshot_date,
                    total_unrealized_pnl=position_summary['total_unrealized_pnl'],
                    total_realized_pnl=position_summary['total_realized_pnl'],
                    total_commission=Decimal('0'),  # TODO: Calculate from executions
                    total_positions=len(positions_data),
                    long_positions=len([p for p in positions_data if p['quantity'] > 0]),
                    short_positions=len([p for p in positions_data if p['quantity'] < 0]),
                    total_market_value=position_summary['total_market_value'],
                    total_cost_basis=position_summary['total_cost_basis'],
                    positions_snapshot=positions_data
                )
                
                snapshots.append(snapshot)
            
            return snapshots[0] if len(snapshots) == 1 else snapshots
    
    def get_pnl_summary(self, broker_account_id: str = None, days: int = 30) -> Dict[str, Any]:
        """Get P&L summary for the last N days."""
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=days)
        
        queryset = PnLSnapshot.objects.filter(
            tenant=self.tenant,
            snapshot_date__gte=start_date,
            snapshot_date__lte=end_date
        )
        
        if broker_account_id:
            queryset = queryset.filter(broker_account_id=broker_account_id)
        
        summary = queryset.aggregate(
            total_unrealized_pnl=Sum('total_unrealized_pnl'),
            total_realized_pnl=Sum('total_realized_pnl'),
            total_commission=Sum('total_commission'),
            total_market_value=Sum('total_market_value'),
            total_cost_basis=Sum('total_cost_basis')
        )
        
        return {
            'period_days': days,
            'start_date': start_date,
            'end_date': end_date,
            'total_unrealized_pnl': summary['total_unrealized_pnl'] or Decimal('0'),
            'total_realized_pnl': summary['total_realized_pnl'] or Decimal('0'),
            'total_commission': summary['total_commission'] or Decimal('0'),
            'total_market_value': summary['total_market_value'] or Decimal('0'),
            'total_cost_basis': summary['total_cost_basis'] or Decimal('0'),
            'net_pnl': (summary['total_unrealized_pnl'] or Decimal('0')) + (summary['total_realized_pnl'] or Decimal('0'))
        }
