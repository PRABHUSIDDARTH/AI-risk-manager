"""
Scorer service: loads the trained sklearn pipeline and returns a risk score.
NOTE: This module does NOT import from ml/ - it handles feature preparation inline
to keep backend self-contained.
"""
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from functools import lru_cache
from ..config import settings

FEATURE_COLS = [
    'order_value', 'num_items', 'category', 'payment_method',
    'customer_return_rate', 'days_to_deliver', 'seller_rating',
    'is_first_order', 'discount_pct', 'pincode_return_rate',
    'hour_of_order', 'device_type'
]

@lru_cache(maxsize=1)
def _load_model():
    model_path = Path(settings.MODEL_PATH)
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Run ml/train.py first.")
    return joblib.load(model_path)

@lru_cache(maxsize=1)
def get_model_version() -> str:
    ver_path = Path(settings.MODEL_VERSION_PATH)
    if ver_path.exists():
        return ver_path.read_text().strip()
    return "unknown"

def score_order(order_dict: dict) -> float:
    """Score a single order dict and return probability of return (0-1)."""
    model = _load_model()
    row = {col: [order_dict[col]] for col in FEATURE_COLS}
    df = pd.DataFrame(row)
    df['is_first_order'] = df['is_first_order'].astype(int)
    prob = model.predict_proba(df)[0][1]
    return float(prob)

def is_model_loaded() -> bool:
    try:
        _load_model()
        return True
    except Exception:
        return False
