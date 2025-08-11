"""
OMS API v1 endpoints.
"""

from ninja import Router, Query
from ninja.pagination import paginate
from typing import List, Optional, Any
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.db import transaction

from apps.api.base import api_controller
from apps.api.schemas import (
    ResponseSchema, ErrorResponseSchema, PaginatedResponseSchema,
    IdempotencyKeyHeader, ETagHeader
)
from apps.oms.schemas import (
    OrderCreateSchema, OrderUpdateSchema, OrderResponseSchema, OrderFilterSchema,
    OrderListResponseSchema, BulkOrderCreateSchema, BulkOrderResponseSchema,
    ExecutionResponseSchema, ExecutionFilterSchema, ExecutionListResponseSchema,
    PositionResponseSchema, PositionFilterSchema, PositionListResponseSchema,
    PnLSnapshotResponseSchema, PnLFilterSchema, PnLListResponseSchema,
    BulkCancelSchema, BulkCancelResponseSchema
)
from apps.oms.models import Order, Execution, Position, PnLSnapshot
from apps.oms.services import OrderService, ExecutionService, PositionService, PnLService
from apps.core.models import User
from apps.tenants.models import Tenant


router = Router()


@router.get("/orders", response=OrderListResponseSchema, summary="List Orders")
@api_controller
def list_orders(
    request: HttpRequest,
    query: Query[OrderFilterSchema],
    tenant: Any = None,
    user: Any = None
):
    """
    List orders with filtering and pagination.
    
    Supports filtering by:
    - Instrument symbol
    - Broker account
    - Order type and side
    - Strategy run
    - User
    - Status and date range
    """
    service = OrderService(tenant=tenant, user=user)
    orders, total_count, has_next = service.list_orders(
        filters=query.dict(exclude_none=True),
        limit=query.limit,
        offset=query.offset
    )
    
    return OrderListResponseSchema(
        orders=orders,
        total_count=total_count,
        has_next=has_next
    )


@router.post("/orders", response=OrderResponseSchema, summary="Create Order")
@api_controller
def create_order(
    request: HttpRequest,
    payload: OrderCreateSchema,
    tenant: Any = None,
    user: Any = None
):
    """
    Create a new order.
    
    Validates order parameters and creates the order in the system.
    Returns the created order with all details.
    """
    service = OrderService(tenant=tenant, user=user)
    order = service.create_order(payload.dict())
    
    return OrderResponseSchema.from_orm(order)


@router.post("/orders/bulk", response=BulkOrderResponseSchema, summary="Create Bulk Orders")
@api_controller
def create_bulk_orders(
    request: HttpRequest,
    payload: BulkOrderCreateSchema,
    idempotency_key: IdempotencyKeyHeader,
    tenant: Any = None,
    user: Any = None
):
    """
    Create multiple orders in a single request.
    
    Uses idempotency key to prevent duplicate creation.
    Returns accepted and rejected orders with error details.
    """
    service = OrderService(tenant=tenant, user=user)
    result = service.create_bulk_orders(
        orders=payload.orders,
        idempotency_key=idempotency_key
    )
    
    return BulkOrderResponseSchema(
        accepted=result['accepted'],
        rejected=result['rejected']
    )


@router.get("/orders/{order_id}", response=OrderResponseSchema, summary="Get Order")
@api_controller
def get_order(
    request: HttpRequest,
    order_id: str,
    tenant: Any = None,
    user: Any = None
):
    """
    Get order details by ID.
    
    Returns complete order information including execution details.
    """
    service = OrderService(tenant=tenant, user=user)
    order = service.get_order(order_id)
    
    return OrderResponseSchema.from_orm(order)


@router.put("/orders/{order_id}", response=OrderResponseSchema, summary="Update Order")
@api_controller
def update_order(
    request: HttpRequest,
    order_id: str,
    payload: OrderUpdateSchema,
    etag: ETagHeader,
    tenant: Any = None,
    user: Any = None
):
    """
    Update an existing order.
    
    Uses ETag for optimistic concurrency control.
    Only allows updates to certain fields.
    """
    service = OrderService(tenant=tenant, user=user)
    order = service.update_order(
        order_id=order_id,
        updates=payload.dict(exclude_none=True),
        etag=etag
    )
    
    return OrderResponseSchema.from_orm(order)


@router.delete("/orders/{order_id}", response=ResponseSchema, summary="Cancel Order")
@api_controller
def cancel_order(
    request: HttpRequest,
    order_id: str,
    tenant: Any = None,
    user: Any = None
):
    """
    Cancel an existing order.
    
    Only allows cancellation of orders in certain states.
    Returns success confirmation.
    """
    service = OrderService(tenant=tenant, user=user)
    service.cancel_order(order_id)
    
    return ResponseSchema(message="Order cancelled successfully")


@router.post("/orders/bulk/cancel", response=BulkCancelResponseSchema, summary="Cancel Bulk Orders")
@api_controller
def cancel_bulk_orders(
    request: HttpRequest,
    payload: BulkCancelSchema,
    idempotency_key: IdempotencyKeyHeader,
    tenant: Any = None,
    user: Any = None
):
    """
    Cancel multiple orders in a single request.
    
    Uses idempotency key to prevent duplicate cancellation.
    Returns accepted and rejected cancellations with error details.
    """
    service = OrderService(tenant=tenant, user=user)
    result = service.cancel_bulk_orders(
        order_ids=payload.order_ids,
        idempotency_key=idempotency_key
    )
    
    return BulkCancelResponseSchema(
        accepted=result['accepted'],
        rejected=result['rejected']
    )


@router.get("/executions", response=ExecutionListResponseSchema, summary="List Executions")
@api_controller
def list_executions(
    request: HttpRequest,
    query: Query[ExecutionFilterSchema],
    tenant: Any = None,
    user: Any = None
):
    """
    List executions with filtering and pagination.
    
    Supports filtering by:
    - Order ID
    - Instrument symbol
    - Broker account
    - Date range
    """
    service = ExecutionService(tenant=tenant, user=user)
    executions, total_count, has_next = service.list_executions(
        filters=query.dict(exclude_none=True),
        limit=query.limit,
        offset=query.offset
    )
    
    return ExecutionListResponseSchema(
        executions=executions,
        total_count=total_count,
        has_next=has_next
    )


@router.get("/executions/{execution_id}", response=ExecutionResponseSchema, summary="Get Execution")
@api_controller
def get_execution(
    request: HttpRequest,
    execution_id: str,
    tenant: Any = None,
    user: Any = None
):
    """
    Get execution details by ID.
    
    Returns complete execution information.
    """
    service = ExecutionService(tenant=tenant, user=user)
    execution = service.get_execution(execution_id)
    
    return ExecutionResponseSchema.from_orm(execution)


@router.get("/positions", response=PositionListResponseSchema, summary="List Positions")
@api_controller
def list_positions(
    request: HttpRequest,
    query: Query[PositionFilterSchema],
    tenant: Any = None,
    user: Any = None
):
    """
    List positions with filtering and pagination.
    
    Supports filtering by:
    - Instrument symbol
    - Broker account
    - Position existence
    """
    service = PositionService(tenant=tenant, user=user)
    positions, total_count, has_next = service.list_positions(
        filters=query.dict(exclude_none=True),
        limit=query.limit,
        offset=query.offset
    )
    
    return PositionListResponseSchema(
        positions=positions,
        total_count=total_count,
        has_next=has_next
    )


@router.get("/positions/{position_id}", response=PositionResponseSchema, summary="Get Position")
@api_controller
def get_position(
    request: HttpRequest,
    position_id: str,
    tenant: Any = None,
    user: Any = None
):
    """
    Get position details by ID.
    
    Returns complete position information including P&L.
    """
    service = PositionService(tenant=tenant, user=user)
    position = service.get_position(position_id)
    
    return PositionResponseSchema.from_orm(position)


@router.get("/pnl", response=PnLListResponseSchema, summary="List P&L Snapshots")
@api_controller
def list_pnl_snapshots(
    request: HttpRequest,
    query: Query[PnLFilterSchema],
    tenant: Any = None,
    user: Any = None
):
    """
    List P&L snapshots with filtering and pagination.
    
    Supports filtering by:
    - Broker account
    - Date range
    """
    service = PnLService(tenant=tenant, user=user)
    snapshots, total_count, has_next = service.list_pnl_snapshots(
        filters=query.dict(exclude_none=True),
        limit=query.limit,
        offset=query.offset
    )
    
    return PnLListResponseSchema(
        snapshots=snapshots,
        total_count=total_count,
        has_next=has_next
    )


@router.get("/pnl/{snapshot_id}", response=PnLSnapshotResponseSchema, summary="Get P&L Snapshot")
@api_controller
def get_pnl_snapshot(
    request: HttpRequest,
    snapshot_id: str,
    tenant: Any = None,
    user: Any = None
):
    """
    Get P&L snapshot details by ID.
    
    Returns complete P&L information including position breakdown.
    """
    service = PnLService(tenant=tenant, user=user)
    snapshot = service.get_pnl_snapshot(snapshot_id)
    
    return PnLSnapshotResponseSchema.from_orm(snapshot)


@router.post("/pnl/snapshot", response=PnLSnapshotResponseSchema, summary="Create P&L Snapshot")
@api_controller
def create_pnl_snapshot(
    request: HttpRequest,
    tenant: Any = None,
    user: Any = None
):
    """
    Create a new P&L snapshot.
    
    Calculates current P&L for all positions and creates a snapshot.
    """
    service = PnLService(tenant=tenant, user=user)
    snapshot = service.create_snapshot()
    
    return PnLSnapshotResponseSchema.from_orm(snapshot)
