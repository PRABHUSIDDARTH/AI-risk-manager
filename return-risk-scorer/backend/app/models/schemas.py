from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, Any
from ..services.normalizer import (
    normalize_category,
    normalize_payment_method,
    normalize_device_type,
    parse_rate,
    parse_numeric,
    parse_hour
)

class OrderRequest(BaseModel):
    order_id: str
    order_value: float = Field(gt=0)
    num_items: int = Field(default=1, ge=1, le=50)
    category: str = Field(default='apparel')
    payment_method: str = Field(default='prepaid')
    customer_return_rate: float = Field(default=0.15, ge=0.0, le=1.0)
    days_to_deliver: int = Field(default=4, ge=1, le=30)
    seller_rating: float = Field(default=4.2, ge=1.0, le=5.0)
    is_first_order: bool = Field(default=False)
    discount_pct: float = Field(default=0.10, ge=0.0, le=1.0)
    pincode_return_rate: float = Field(default=0.18, ge=0.0, le=1.0)
    hour_of_order: int = Field(default=14, ge=0, le=23)
    device_type: str = Field(default='mobile')

    @field_validator('category', mode='before')
    @classmethod
    def validate_category(cls, v: Any) -> str:
        return normalize_category(v)

    @field_validator('payment_method', mode='before')
    @classmethod
    def validate_payment_method(cls, v: Any) -> str:
        return normalize_payment_method(v)

    @field_validator('device_type', mode='before')
    @classmethod
    def validate_device_type(cls, v: Any) -> str:
        return normalize_device_type(v)

    @field_validator('customer_return_rate', 'discount_pct', 'pincode_return_rate', mode='before')
    @classmethod
    def validate_rates(cls, v: Any) -> float:
        return parse_rate(v, default=0.15)

    @field_validator('order_value', mode='before')
    @classmethod
    def validate_order_value(cls, v: Any) -> Any:
        if isinstance(v, (int, float)):
            return v
        return parse_numeric(v, default=-1.0)

    @field_validator('num_items', mode='before')
    @classmethod
    def validate_num_items(cls, v: Any) -> Any:
        if isinstance(v, (int, float)):
            return int(v)
        return int(parse_numeric(v, default=1, min_val=1, max_val=50))

    @field_validator('hour_of_order', mode='before')
    @classmethod
    def validate_hour(cls, v: Any) -> int:
        return parse_hour(v, default=14)


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
