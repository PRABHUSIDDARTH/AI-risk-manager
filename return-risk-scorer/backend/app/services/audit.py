import json
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.orm import Order, Prediction, Action, AuditLog

def write_audit_log(
    db: Session,
    order_dict: dict,
    score: float,
    explanation: str,
    action: str,
    model_version: str
) -> int:
    """Write a complete audit trail entry. Returns the audit_log id."""
    order_id = order_dict['order_id']
    now = datetime.utcnow()
    
    # Upsert Order
    existing_order = db.query(Order).filter(Order.order_id == order_id).first()
    if not existing_order:
        db_order = Order(
            order_id=order_id,
            order_value=order_dict['order_value'],
            num_items=order_dict['num_items'],
            category=order_dict['category'],
            payment_method=order_dict['payment_method'],
            customer_return_rate=order_dict['customer_return_rate'],
            days_to_deliver=order_dict['days_to_deliver'],
            seller_rating=order_dict['seller_rating'],
            is_first_order=order_dict['is_first_order'],
            discount_pct=order_dict['discount_pct'],
            pincode_return_rate=order_dict['pincode_return_rate'],
            hour_of_order=order_dict['hour_of_order'],
            device_type=order_dict['device_type'],
            created_at=now
        )
        db.add(db_order)
    
    # Prediction record
    db_pred = Prediction(order_id=order_id, score=score, model_version=model_version, created_at=now)
    db.add(db_pred)
    
    # Action record
    db_action = Action(order_id=order_id, action=action, created_at=now)
    db.add(db_action)
    
    # Audit log - main auditable record
    audit_entry = AuditLog(
        order_id=order_id,
        timestamp=now,
        input_features=json.dumps(order_dict),
        score=score,
        explanation=explanation,
        action=action,
        model_version=model_version
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry.id
