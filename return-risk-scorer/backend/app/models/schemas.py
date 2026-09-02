from pydantic import BaseModel, Field
from typing import Literal, Optional

class OrderRequest(BaseModel):
    order_id: str
    order_value: float = Field(gt=0)
    num_items: int = Field(ge=1, le=50)
    category: Literal['electronics','apparel','footwear','books','home','beauty']
    payment_method: Literal['cod','prepaid','emi']
    customer_return_rate: float = Field(ge=0.0, le=1.0)
    days_to_deliver: int = Field(ge=1, le=30)
    seller_rating: float = Field(ge=1.0, le=5.0)
    is_first_order: bool
    discount_pct: float = Field(ge=0.0, le=1.0)
    pincode_return_rate: float = Field(ge=0.0, le=1.0)
    hour_of_order: int = Field(ge=0, le=23)
    device_type: Literal['mobile','desktop','app']

class ScoreResponse(BaseModel):
    order_id: str
    score: float
    action: str
    explanation: str
    audit_id: int
    model_version: str

class OrderListItem(BaseModel):
    audit_id: int
    order_id: str
    score: float
    action: str
    explanation: str
    category: str
    payment_method: str
    order_value: float
    timestamp: str

class OrderDetail(BaseModel):
    audit_id: int
    order_id: str
    score: float
    action: str
    explanation: str
    model_version: str
    timestamp: str
    input_features: dict

class BatchSummary(BaseModel):
    total: int
    allow_count: int
    flag_count: int
    block_count: int
    avg_score: float

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str
