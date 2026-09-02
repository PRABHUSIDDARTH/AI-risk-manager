from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from datetime import datetime
from .db import Base

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    order_value = Column(Float)
    num_items = Column(Integer)
    category = Column(String)
    payment_method = Column(String)
    customer_return_rate = Column(Float)
    days_to_deliver = Column(Integer)
    seller_rating = Column(Float)
    is_first_order = Column(Boolean)
    discount_pct = Column(Float)
    pincode_return_rate = Column(Float)
    hour_of_order = Column(Integer)
    device_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, index=True)
    score = Column(Float)
    model_version = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Action(Base):
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, index=True)
    action = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    input_features = Column(Text)
    score = Column(Float)
    explanation = Column(Text)
    action = Column(String)
    model_version = Column(String)
