from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import json
from ..models.db import get_db
from ..models.orm import AuditLog
from ..models.schemas import OrderListItem, OrderDetail

router = APIRouter(prefix='/api', tags=['orders'])

@router.get('/orders', response_model=List[OrderListItem])
def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """List all scored orders (paginated)."""
    offset = (page - 1) * limit
    entries = (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    result = []
    for e in entries:
        features = json.loads(e.input_features) if e.input_features else {}
        result.append(OrderListItem(
            audit_id=e.id,
            order_id=e.order_id,
            score=e.score,
            action=e.action,
            explanation=e.explanation,
            category=features.get('category', ''),
            payment_method=features.get('payment_method', ''),
            order_value=features.get('order_value', 0.0),
            timestamp=e.timestamp.isoformat() if e.timestamp else '',
        ))
    return result

@router.get('/orders/{order_id}', response_model=OrderDetail)
def get_order(order_id: str, db: Session = Depends(get_db)):
    """Get full detail for a specific order."""
    entry = (
        db.query(AuditLog)
        .filter(AuditLog.order_id == order_id)
        .order_by(AuditLog.timestamp.desc())
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    features = json.loads(entry.input_features) if entry.input_features else {}
    return OrderDetail(
        audit_id=entry.id,
        order_id=entry.order_id,
        score=entry.score,
        action=entry.action,
        explanation=entry.explanation,
        model_version=entry.model_version,
        timestamp=entry.timestamp.isoformat() if entry.timestamp else '',
        input_features=features,
    )

@router.get('/audit', response_model=List[OrderListItem])
def get_audit_log(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Full audit log with all decisions."""
    offset = (page - 1) * limit
    entries = (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    result = []
    for e in entries:
        features = json.loads(e.input_features) if e.input_features else {}
        result.append(OrderListItem(
            audit_id=e.id,
            order_id=e.order_id,
            score=e.score,
            action=e.action,
            explanation=e.explanation,
            category=features.get('category', ''),
            payment_method=features.get('payment_method', ''),
            order_value=features.get('order_value', 0.0),
            timestamp=e.timestamp.isoformat() if e.timestamp else '',
        ))
    return result
