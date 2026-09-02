from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..models.db import get_db
from ..models.schemas import OrderRequest, ScoreResponse
from ..services import scorer, gemini, audit
from ..config import settings

router = APIRouter(prefix='/api', tags=['scoring'])

@router.post('/score', response_model=ScoreResponse)
def score_order(order: OrderRequest, db: Session = Depends(get_db)):
    """Score a single order for return risk."""
    order_dict = order.model_dump()
    score = scorer.score_order(order_dict)
    explanation, action = gemini.get_explanation_and_action(
        order_dict, score,
        threshold_allow=settings.SCORE_THRESHOLD_ALLOW,
        threshold_block=settings.SCORE_THRESHOLD_BLOCK
    )
    audit_id = audit.write_audit_log(db, order_dict, score, explanation, action, scorer.get_model_version())
    return ScoreResponse(
        order_id=order.order_id,
        score=score,
        action=action,
        explanation=explanation,
        audit_id=audit_id,
        model_version=scorer.get_model_version()
    )
