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
from ..services.normalizer import normalize_order_record
from ..config import settings

router = APIRouter(prefix='/api', tags=['batch'])
logger = logging.getLogger(__name__)


def decode_csv_bytes(raw_bytes: bytes) -> str:
    """Decode raw bytes trying UTF-8, UTF-8-sig, Latin-1, and windows-1252."""
    for enc in ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252'):
        try:
            return raw_bytes.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw_bytes.decode('utf-8', errors='replace')


def read_csv_rows(text: str):
    """Parse CSV text with dialect auto-detection, fallback to comma."""
    sample = text[:4096]
    delimiter = ','
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ','

    f = io.StringIO(text.strip())
    reader = csv.DictReader(f, delimiter=delimiter)
    return list(reader)


@router.post('/batch')
async def batch_score(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Score a batch of orders from a CSV file. Returns NDJSON stream."""
    contents = await file.read()
    text = decode_csv_bytes(contents)
    rows = read_csv_rows(text)
    
    def generate():
        counts = {'allow': 0, 'flag_for_verification': 0, 'block_cod': 0}
        scores = []
        model_version = scorer.get_model_version()
        
        for i, row in enumerate(rows):
            try:
                # Normalize arbitrary CSV columns, formats, and synonyms
                normalized_dict = normalize_order_record(row, index=i)
                order = OrderRequest(**normalized_dict)
                order_payload = order.model_dump()
                
                score_val = scorer.score_order(order_payload)
                explanation, action = gemini.get_explanation_and_action(
                    order_payload, score_val,
                    threshold_allow=settings.SCORE_THRESHOLD_ALLOW,
                    threshold_block=settings.SCORE_THRESHOLD_BLOCK
                )
                audit_id = audit.write_audit_log(
                    db, order_payload, score_val, explanation, action, model_version
                )
                
                counts[action] = counts.get(action, 0) + 1
                scores.append(score_val)
                
                result = {
                    'order_id': order.order_id,
                    'score': round(score_val, 4),
                    'action': action,
                    'explanation': explanation,
                    'audit_id': audit_id,
                    'model_version': model_version,
                    # Display fields required by the results table
                    'order_value': order.order_value,
                    'category': order.category,
                    'payment_method': order.payment_method,
                }
                yield json.dumps(result) + '\n'
                
            except Exception as e:
                logger.warning(f"Error processing row {i}: {e}")
                yield json.dumps({
                    'order_id': row.get('order_id', row.get('id', f'row-{i}')),
                    'error': str(e)
                }) + '\n'
        
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
