import csv
import io
import json
import logging
from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..models.db import get_db
from ..models.schemas import OrderRequest
from ..services import scorer, gemini, audit
from ..config import settings

router = APIRouter(prefix='/api', tags=['batch'])
logger = logging.getLogger(__name__)

@router.post('/batch')
async def batch_score(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Score a batch of orders from a CSV file. Returns NDJSON stream."""
    contents = await file.read()
    text = contents.decode('utf-8')
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    
    def generate():
        counts = {'allow': 0, 'flag_for_verification': 0, 'block_cod': 0}
        scores = []
        model_version = scorer.get_model_version()
        
        for i, row in enumerate(rows):
            try:
                # Type coerce CSV strings to correct types
                order_dict = {
                    'order_id': str(row.get('order_id', f'batch-{i}')),
                    'order_value': float(row['order_value']),
                    'num_items': int(row['num_items']),
                    'category': str(row['category']),
                    'payment_method': str(row['payment_method']),
                    'customer_return_rate': float(row['customer_return_rate']),
                    'days_to_deliver': int(row['days_to_deliver']),
                    'seller_rating': float(row['seller_rating']),
                    'is_first_order': str(row['is_first_order']).lower() in ('true','1','yes'),
                    'discount_pct': float(row['discount_pct']),
                    'pincode_return_rate': float(row['pincode_return_rate']),
                    'hour_of_order': int(row['hour_of_order']),
                    'device_type': str(row['device_type']),
                }
                order = OrderRequest(**order_dict)
                score_val = scorer.score_order(order.model_dump())
                explanation, action = gemini.get_explanation_and_action(
                    order.model_dump(), score_val,
                    threshold_allow=settings.SCORE_THRESHOLD_ALLOW,
                    threshold_block=settings.SCORE_THRESHOLD_BLOCK
                )
                audit_id = audit.write_audit_log(db, order.model_dump(), score_val, explanation, action, model_version)
                
                counts[action] = counts.get(action, 0) + 1
                scores.append(score_val)
                
                result = {
                    'order_id': order.order_id,
                    'score': round(score_val, 4),
                    'action': action,
                    'explanation': explanation,
                    'audit_id': audit_id,
                    'model_version': model_version,
                    # Display fields needed by the results table
                    'order_value': order.order_value,
                    'category': order.category,
                    'payment_method': order.payment_method,
                }
                yield json.dumps(result) + '\n'
                
            except Exception as e:
                logger.warning(f"Skipping row {i}: {e}")
                yield json.dumps({'order_id': row.get('order_id', f'row-{i}'), 'error': str(e)}) + '\n'
        
        # Final summary line
        summary = {
            '_summary': True,
            'total': len(rows),
            'allow_count': counts.get('allow', 0),
            'flag_count': counts.get('flag_for_verification', 0),
            'block_count': counts.get('block_cod', 0),
            'avg_score': round(sum(scores) / len(scores), 4) if scores else 0.0,
        }
        yield json.dumps(summary) + '\n'
    
    return StreamingResponse(generate(), media_type='application/x-ndjson')
