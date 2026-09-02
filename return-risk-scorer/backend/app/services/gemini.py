"""
Gemini LLM service: generates human-readable explanation and recommends action.
Falls back to rule-based explanation if API key is not set or call fails.
"""
import json
import logging
from ..config import settings

logger = logging.getLogger(__name__)

ACTION_ALLOW = "allow"
ACTION_FLAG = "flag_for_verification"
ACTION_BLOCK = "block_cod"

def _rule_based_fallback(order_dict: dict, score: float, threshold_allow: float, threshold_block: float) -> tuple[str, str]:
    """Generate a rule-based explanation when Gemini is unavailable."""
    risk_factors = []
    if order_dict.get('payment_method') == 'cod':
        risk_factors.append("cash-on-delivery payment")
    if order_dict.get('customer_return_rate', 0) > 0.4:
        risk_factors.append(f"high customer return history ({order_dict['customer_return_rate']:.0%})")
    if order_dict.get('discount_pct', 0) > 0.4:
        risk_factors.append(f"large discount ({order_dict['discount_pct']:.0%})")
    if order_dict.get('category') in ['electronics', 'footwear']:
        risk_factors.append(f"{order_dict['category']} category has elevated return rates")
    if order_dict.get('days_to_deliver', 0) > 7:
        risk_factors.append("extended delivery window")
    if order_dict.get('is_first_order'):
        risk_factors.append("first-time customer")
    if order_dict.get('pincode_return_rate', 0) > 0.4:
        risk_factors.append("high-return geographic area")
    
    if not risk_factors:
        explanation = f"This order has a low return risk score of {score:.1%}. No significant risk factors were detected."
    elif len(risk_factors) == 1:
        explanation = f"This order has a {score:.1%} return probability. The primary signal is {risk_factors[0]}."
    else:
        factors_str = ', '.join(risk_factors[:3])
        explanation = f"This order has a {score:.1%} return probability, driven by: {factors_str}. These combined signals elevate the return risk."
    
    if score < threshold_allow:
        action = ACTION_ALLOW
    elif score < threshold_block:
        action = ACTION_FLAG
    else:
        action = ACTION_BLOCK
    
    return explanation, action

def get_explanation_and_action(
    order_dict: dict,
    score: float,
    threshold_allow: float = 0.35,
    threshold_block: float = 0.65
) -> tuple[str, str]:
    """Call Gemini to get explanation + action. Falls back to rule-based if unavailable."""
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set, using rule-based fallback")
        return _rule_based_fallback(order_dict, score, threshold_allow, threshold_block)
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        features_str = "\n".join([
            f"  - Order Value: ₹{order_dict.get('order_value', 0):.2f}",
            f"  - Items: {order_dict.get('num_items', 1)}",
            f"  - Category: {order_dict.get('category', 'unknown')}",
            f"  - Payment: {order_dict.get('payment_method', 'unknown')}",
            f"  - Customer Return History: {order_dict.get('customer_return_rate', 0):.1%}",
            f"  - Days to Deliver: {order_dict.get('days_to_deliver', 1)}",
            f"  - Seller Rating: {order_dict.get('seller_rating', 5.0):.1f}/5",
            f"  - First Order: {'Yes' if order_dict.get('is_first_order') else 'No'}",
            f"  - Discount: {order_dict.get('discount_pct', 0):.1%}",
            f"  - Pincode Return Rate: {order_dict.get('pincode_return_rate', 0):.1%}",
            f"  - Hour of Order: {order_dict.get('hour_of_order', 12)}:00",
            f"  - Device: {order_dict.get('device_type', 'mobile')}",
        ])
        
        prompt = f"""You are an AI risk analyst for an e-commerce platform's return risk system.

Order details:
{features_str}

ML model risk score: {score:.1%} (probability this order will be returned/refunded)

Threshold guidance:
- Score < {threshold_allow:.0%}: LOW RISK → allow
- Score {threshold_allow:.0%} to {threshold_block:.0%}: MEDIUM RISK → flag_for_verification  
- Score > {threshold_block:.0%}: HIGH RISK → block_cod

Analyze the key risk factors present in this order and explain in 2-3 clear sentences why it received this risk score. Be specific about which features are driving the risk.

Respond with ONLY valid JSON in this exact format:
{{"explanation": "2-3 sentence explanation here", "action": "allow|flag_for_verification|block_cod"}}"""
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Strip markdown code fences if present
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        text = text.strip()
        
        result = json.loads(text)
        explanation = result.get('explanation', '')
        action = result.get('action', '')
        
        # Validate action
        valid_actions = [ACTION_ALLOW, ACTION_FLAG, ACTION_BLOCK]
        if action not in valid_actions:
            # Fallback to threshold-based action
            if score < threshold_allow:
                action = ACTION_ALLOW
            elif score < threshold_block:
                action = ACTION_FLAG
            else:
                action = ACTION_BLOCK
        
        return explanation, action
    
    except Exception as e:
        logger.error(f"Gemini API error: {e}. Using fallback.")
        return _rule_based_fallback(order_dict, score, threshold_allow, threshold_block)
