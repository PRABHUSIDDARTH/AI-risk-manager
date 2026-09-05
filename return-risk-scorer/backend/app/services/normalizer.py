"""
Normalizer service: provides robust normalization and schema adaptation for
e-commerce order records from any CSV format, column naming convention, or external system.
"""
import re
from typing import Any, Dict, Optional
from datetime import datetime

# Canonical categories recognized by ML model
CANONICAL_CATEGORIES = {'electronics', 'apparel', 'footwear', 'books', 'home', 'beauty'}

CATEGORY_SYNONYMS = {
    'apparel': ['clothing', 'clothes', 'fashion', 'wear', 'garments', 'textile', 'shirt', 'dress', 'jeans', 'tshirt', 'apparel', 'apparel & fashion'],
    'electronics': ['electronics', 'gadgets', 'tech', 'mobile', 'phone', 'cellphone', 'laptop', 'computer', 'audio', 'headphones', 'camera', 'tv', 'accessories', 'smartwatch', 'hardware'],
    'footwear': ['footwear', 'shoes', 'sneakers', 'sandals', 'boots', 'slippers', 'loafers', 'heels', 'flats'],
    'books': ['books', 'book', 'stationery', 'novel', 'literature', 'reading', 'paperback', 'hardcover', 'comics', 'textbook'],
    'home': ['home', 'kitchen', 'furniture', 'decor', 'appliances', 'living', 'bedding', 'bath', 'lighting', 'cookware', 'storage', 'household'],
    'beauty': ['beauty', 'cosmetics', 'skincare', 'makeup', 'fragrance', 'perfume', 'haircare', 'grooming', 'personal care', 'personal_care', 'wellness']
}

# Mapping aliases to canonical field keys
FIELD_ALIASES = {
    'order_id': [
        'order_id', 'orderid', 'order_no', 'orderno', 'order_number', 'ordernumber',
        'id', 'invoice_id', 'invoiceno', 'invoice_no', 'ref', 'reference', 'txn_id', 'transaction_id'
    ],
    'order_value': [
        'order_value', 'ordervalue', 'order_amount', 'orderamount', 'amount', 'total_amount',
        'totalamount', 'total_price', 'price', 'total', 'value', 'grand_total', 'net_amount',
        'sale_amount', 'order_total', 'item_price', 'subtotal'
    ],
    'num_items': [
        'num_items', 'numitems', 'items', 'item_count', 'itemcount', 'items_count',
        'quantity', 'qty', 'units', 'num_of_items', 'total_items', 'line_items'
    ],
    'category': [
        'category', 'product_category', 'prod_category', 'cat', 'department',
        'dept', 'item_category', 'product_type', 'type', 'genre', 'vertical'
    ],
    'payment_method': [
        'payment_method', 'paymentmethod', 'payment_type', 'paymenttype', 'payment',
        'pay_mode', 'paymode', 'mode_of_payment', 'method', 'payment_mode', 'gateway'
    ],
    'customer_return_rate': [
        'customer_return_rate', 'customerreturnrate', 'return_rate', 'returnrate',
        'cust_return_rate', 'user_return_rate', 'past_returns', 'historic_return_rate',
        'buyer_return_rate', 'customer_refund_rate'
    ],
    'days_to_deliver': [
        'days_to_deliver', 'daystodeliver', 'delivery_days', 'shipping_days',
        'transit_days', 'lead_time', 'days', 'sla_days', 'expected_delivery_days', 'tat'
    ],
    'seller_rating': [
        'seller_rating', 'sellerrating', 'seller_score', 'merchant_rating',
        'vendor_rating', 'rating', 'seller_stars', 'store_rating'
    ],
    'is_first_order': [
        'is_first_order', 'isfirstorder', 'first_order', 'firstorder', 'new_customer',
        'is_new_customer', 'new_user', 'is_new_user', 'first_purchase', 'first_time'
    ],
    'discount_pct': [
        'discount_pct', 'discountpct', 'discount', 'discount_percent', 'discount_percentage',
        'discount_rate', 'disc_pct', 'promo_discount', 'coupon_discount', 'rebate'
    ],
    'pincode_return_rate': [
        'pincode_return_rate', 'pincodereturnrate', 'pin_return_rate', 'zipcode_return_rate',
        'zip_return_rate', 'postal_return_rate', 'area_return_rate', 'pincode_risk', 'location_risk'
    ],
    'hour_of_order': [
        'hour_of_order', 'houroforder', 'order_hour', 'orderhour', 'hour', 'time',
        'created_hour', 'timestamp', 'created_at', 'order_time', 'order_date', 'date'
    ],
    'device_type': [
        'device_type', 'devicetype', 'device', 'platform', 'client', 'source', 'channel', 'os'
    ]
}


def clean_header_key(key: str) -> str:
    """Normalize a header string: strip, lowercase, replace spaces/hyphens with underscores."""
    if not isinstance(key, str):
        return ""
    clean = re.sub(r'[\s\-]+', '_', key.strip().lower())
    return re.sub(r'[^a-z0-9_]', '', clean)


def parse_numeric(val: Any, default: float, min_val: Optional[float] = None, max_val: Optional[float] = None) -> float:
    """Extract float from arbitrary string or number, stripping currency symbols and commas."""
    if val is None or val == "":
        return default
    if isinstance(val, (int, float)):
        res = float(val)
    else:
        s = str(val).strip()
        # Remove currency symbols and formatting commas
        s = re.sub(r'[₹$€£,A-Za-z\s]', '', s)
        try:
            res = float(s)
        except ValueError:
            return default
    
    if min_val is not None:
        res = max(min_val, res)
    if max_val is not None:
        res = min(max_val, res)
    return res


def parse_rate(val: Any, default: float) -> float:
    """Parse percentage or fractional rate between 0.0 and 1.0."""
    if val is None or val == "":
        return default
    if isinstance(val, (int, float)):
        v = float(val)
        return min(1.0, max(0.0, v / 100.0 if v > 1.0 else v))
    s = str(val).strip()
    is_pct = '%' in s
    s = re.sub(r'[%₹$€£\s]', '', s)
    try:
        v = float(s)
        if is_pct or v > 1.0:
            v /= 100.0
        return min(1.0, max(0.0, v))
    except ValueError:
        return default


def normalize_category(val: Any) -> str:
    """Normalize category to one of the canonical categories recognized by the model."""
    if not val:
        return 'apparel'
    s = str(val).strip().lower()
    if s in CANONICAL_CATEGORIES:
        return s
    for canon, syns in CATEGORY_SYNONYMS.items():
        if any(syn in s for syn in syns):
            return canon
    return 'apparel'


def normalize_payment_method(val: Any) -> str:
    """Normalize payment method to 'cod', 'prepaid', or 'emi'."""
    if not val:
        return 'prepaid'
    s = str(val).strip().lower()
    if 'cod' in s or 'cash' in s or 'delivery' in s:
        return 'cod'
    if 'emi' in s or 'bnpl' in s or 'paylater' in s or 'installment' in s:
        return 'emi'
    return 'prepaid'


def normalize_device_type(val: Any) -> str:
    """Normalize device type to 'mobile', 'desktop', or 'app'."""
    if not val:
        return 'mobile'
    s = str(val).strip().lower()
    if any(k in s for k in ['app', 'ios', 'android', 'apk']):
        return 'app'
    if any(k in s for k in ['desk', 'web', 'pc', 'mac', 'windows', 'browser', 'laptop']):
        return 'desktop'
    return 'mobile'


def parse_hour(val: Any, default: int = 14) -> int:
    """Extract hour (0-23) from integer, time string, or ISO timestamp."""
    if val is None or val == "":
        return default
    if isinstance(val, int) or (isinstance(val, float) and val.is_integer()):
        return int(max(0, min(23, int(val))))
    s = str(val).strip()
    # Try ISO/datetime parsing
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%H:%M:%S', '%H:%M'):
        try:
            return datetime.strptime(s.split('.')[0], fmt).hour
        except ValueError:
            pass
    # Fallback to regex digit extraction
    digits = re.findall(r'\d+', s)
    if digits:
        h = int(digits[0])
        return max(0, min(23, h))
    return default


def normalize_order_record(raw_row: Dict[str, Any], index: int = 0) -> Dict[str, Any]:
    """
    Normalizes a raw dictionary row (from CSV DictReader or external API payload)
    into a complete, validated model-ready feature dictionary.
    """
    cleaned_input = {clean_header_key(k): v for k, v in raw_row.items() if k is not None}
    
    def get_field_val(canonical_name: str) -> Any:
        aliases = FIELD_ALIASES.get(canonical_name, [canonical_name])
        for a in aliases:
            if a in cleaned_input and cleaned_input[a] not in (None, ""):
                return cleaned_input[a]
        return None

    # 1. Order ID
    raw_id = get_field_val('order_id')
    order_id = str(raw_id).strip() if raw_id else f"ORD-{index + 1:04d}"

    # 2. Order Value (min 10.0, default 1250.0)
    raw_val = get_field_val('order_value')
    order_value = parse_numeric(raw_val, default=1250.0, min_val=10.0, max_val=100000.0)

    # 3. Number of items (default 1)
    raw_items = get_field_val('num_items')
    num_items = int(parse_numeric(raw_items, default=1, min_val=1, max_val=50))

    # 4. Category
    raw_cat = get_field_val('category')
    category = normalize_category(raw_cat)

    # 5. Payment method
    raw_pay = get_field_val('payment_method')
    payment_method = normalize_payment_method(raw_pay)

    # 6. Customer return rate (default 0.15)
    raw_crr = get_field_val('customer_return_rate')
    customer_return_rate = parse_rate(raw_crr, default=0.15)

    # 7. Days to deliver (default 4)
    raw_dtd = get_field_val('days_to_deliver')
    days_to_deliver = int(parse_numeric(raw_dtd, default=4, min_val=1, max_val=30))

    # 8. Seller rating (default 4.2)
    raw_sr = get_field_val('seller_rating')
    seller_rating = parse_numeric(raw_sr, default=4.2, min_val=1.0, max_val=5.0)

    # 9. Is first order (default False)
    raw_fo = get_field_val('is_first_order')
    if raw_fo is not None:
        s_fo = str(raw_fo).strip().lower()
        is_first_order = s_fo in ('true', '1', 'yes', 'y', 't', 'first')
    else:
        is_first_order = False

    # 10. Discount percentage (default 0.10)
    raw_disc = get_field_val('discount_pct')
    discount_pct = parse_rate(raw_disc, default=0.10)

    # 11. Pincode return rate (default 0.18)
    raw_prr = get_field_val('pincode_return_rate')
    pincode_return_rate = parse_rate(raw_prr, default=0.18)

    # 12. Hour of order (default 14)
    raw_hour = get_field_val('hour_of_order')
    hour_of_order = parse_hour(raw_hour, default=14)

    # 13. Device type (default mobile)
    raw_dev = get_field_val('device_type')
    device_type = normalize_device_type(raw_dev)

    return {
        'order_id': order_id,
        'order_value': float(round(order_value, 2)),
        'num_items': num_items,
        'category': category,
        'payment_method': payment_method,
        'customer_return_rate': float(round(customer_return_rate, 4)),
        'days_to_deliver': days_to_deliver,
        'seller_rating': float(round(seller_rating, 2)),
        'is_first_order': is_first_order,
        'discount_pct': float(round(discount_pct, 4)),
        'pincode_return_rate': float(round(pincode_return_rate, 4)),
        'hour_of_order': hour_of_order,
        'device_type': device_type,
    }
