import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

SAMPLE_ORDER = {
    "order_id": "test-001",
    "order_value": 1500.0,
    "num_items": 2,
    "category": "electronics",
    "payment_method": "cod",
    "customer_return_rate": 0.4,
    "days_to_deliver": 5,
    "seller_rating": 3.5,
    "is_first_order": False,
    "discount_pct": 0.2,
    "pincode_return_rate": 0.3,
    "hour_of_order": 14,
    "device_type": "mobile"
}

@pytest.fixture
def client():
    with patch('backend.app.services.scorer._load_model') as mock_model, \
         patch('backend.app.services.scorer.get_model_version', return_value='test-v1'), \
         patch('backend.app.services.gemini.get_explanation_and_action', 
               return_value=('Test explanation.', 'flag_for_verification')):
        mock_pipeline = MagicMock()
        mock_pipeline.predict_proba.return_value = [[0.4, 0.6]]
        mock_model.return_value = mock_pipeline
        from backend.app.main import app
        yield TestClient(app)

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'

def test_score_endpoint_valid_order(client):
    response = client.post('/api/score', json=SAMPLE_ORDER)
    assert response.status_code == 200
    data = response.json()
    assert 'score' in data
    assert 'action' in data
    assert 'explanation' in data
    assert 'audit_id' in data
    assert data['action'] in ['allow', 'flag_for_verification', 'block_cod']

def test_score_endpoint_flexible_synonyms(client):
    # Single order with alternative payment method (UPI), category synonym, and minimal fields
    flexible_order = {
        "order_id": "flex-001",
        "order_value": 2499.0,
        "category": "Fashion",
        "payment_method": "UPI",
        "discount_pct": 0.25
    }
    response = client.post('/api/score', json=flexible_order)
    assert response.status_code == 200
    data = response.json()
    assert data['order_id'] == 'flex-001'
    assert 'score' in data

def test_score_endpoint_invalid_payload(client):
    response = client.post('/api/score', json={'order_id': 'bad', 'order_value': -100})
    assert response.status_code == 422  # Validation error

def test_batch_endpoint_with_csv(client):
    import io
    import csv
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(SAMPLE_ORDER.keys()))
    writer.writeheader()
    writer.writerow(SAMPLE_ORDER)
    csv_content = output.getvalue()
    response = client.post(
        '/api/batch',
        files={'file': ('test.csv', csv_content.encode(), 'text/csv')}
    )
    assert response.status_code == 200

def test_batch_endpoint_with_nonstandard_csv(client):
    # Tests arbitrary column headers, currency symbols, percentages, and missing columns
    custom_csv = (
        "Order ID,Amount,Product Category,Payment Mode,Discount %\n"
        "ORD-991,\"₹3,499.00\",Clothing,Cash On Delivery,25%\n"
        "ORD-992,\"$45.00\",Smartphones,Credit Card,10%\n"
    )
    response = client.post(
        '/api/batch',
        files={'file': ('orders.csv', custom_csv.encode('utf-8-sig'), 'text/csv')}
    )
    assert response.status_code == 200
    lines = [json.loads(line) for line in response.text.strip().split('\n') if line]
    assert len(lines) == 3  # 2 orders + 1 _summary
    assert lines[0]['order_id'] == 'ORD-991'
    assert lines[0]['payment_method'] == 'cod'
    assert lines[0]['category'] == 'apparel'
    assert lines[0]['order_value'] == 3499.0
    assert lines[1]['order_id'] == 'ORD-992'
    assert lines[1]['payment_method'] == 'prepaid'
    assert lines[1]['category'] == 'electronics'
    assert lines[2]['_summary'] is True
    assert lines[2]['total'] == 2

def test_batch_endpoint_semicolon_delimited(client):
    # Semicolon delimited CSV format common in European systems
    semi_csv = (
        "id;price;category;payment;items\n"
        "EU-101;1200;Kitchen;Prepaid;2\n"
    )
    response = client.post(
        '/api/batch',
        files={'file': ('eu_orders.csv', semi_csv.encode('latin-1'), 'text/csv')}
    )
    assert response.status_code == 200
    lines = [json.loads(line) for line in response.text.strip().split('\n') if line]
    assert len(lines) == 2
    assert lines[0]['order_id'] == 'EU-101'
    assert lines[0]['category'] == 'home'
    assert lines[0]['order_value'] == 1200.0
