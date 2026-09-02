import numpy as np
import pandas as pd
import uuid
from pathlib import Path
from sklearn.model_selection import StratifiedShuffleSplit

def generate_data():
    np.random.seed(42)
    n = 5000
    
    order_id = [str(uuid.uuid4()) for _ in range(n)]
    order_value = np.clip(np.random.lognormal(mean=6.0, sigma=0.8, size=n), 50, 10000)
    num_items = np.clip(np.random.poisson(lam=2.5, size=n) + 1, 1, 15)
    category = np.random.choice(
        ['electronics','apparel','footwear','books','home','beauty'],
        p=[0.15, 0.25, 0.2, 0.1, 0.2, 0.1],
        size=n
    )
    payment_method = np.random.choice(['cod','prepaid','emi'], p=[0.35,0.55,0.10], size=n)
    customer_return_rate = np.random.beta(a=2, b=5, size=n)
    days_to_deliver = np.clip(np.random.poisson(lam=3, size=n) + 1, 1, 15)
    seller_rating = np.clip(np.random.normal(loc=4.0, scale=0.5, size=n), 1.0, 5.0)
    is_first_order = np.random.binomial(n=1, p=0.2, size=n)
    discount_pct = np.random.beta(a=1, b=4, size=n) * 0.8
    pincode_return_rate = np.random.beta(a=2, b=6, size=n)
    hour_of_order = np.random.randint(0, 24, size=n)
    device_type = np.random.choice(['mobile','desktop','app'], p=[0.45,0.2,0.35], size=n)
    
    def sigmoid(x):
        return 1 / (1 + np.exp(-x))
    
    cat_eff = {'electronics': 0.8, 'apparel': 0.5, 'footwear': 0.7, 'books': -0.3, 'home': 0.1, 'beauty': 0.2}
    pay_eff = {'cod': 1.2, 'emi': 0.3, 'prepaid': 0.0}
    dev_eff = {'mobile': 0.1, 'desktop': 0.0, 'app': -0.1}
    
    base = np.full(n, -3.0)
    base += 0.0003 * order_value
    base += 0.15 * num_items
    base += np.array([cat_eff[c] for c in category])
    base += np.array([pay_eff[p] for p in payment_method])
    base += 2.5 * customer_return_rate
    base += 0.05 * days_to_deliver
    base += -0.3 * seller_rating
    base += 0.4 * is_first_order
    base += 1.5 * discount_pct
    base += 2.0 * pincode_return_rate
    base += np.where(np.isin(hour_of_order, [22, 23, 0, 1, 2]), 0.3, 0.0)
    base += np.array([dev_eff[d] for d in device_type])
    
    prob = sigmoid(base) + np.random.normal(0, 0.05, size=n)
    prob = np.clip(prob, 0, 1)
    will_return = np.random.binomial(n=1, p=prob)
    
    df = pd.DataFrame({
        'order_id': order_id,
        'order_value': order_value,
        'num_items': num_items,
        'category': category,
        'payment_method': payment_method,
        'customer_return_rate': customer_return_rate,
        'days_to_deliver': days_to_deliver,
        'seller_rating': seller_rating,
        'is_first_order': is_first_order,
        'discount_pct': discount_pct,
        'pincode_return_rate': pincode_return_rate,
        'hour_of_order': hour_of_order,
        'device_type': device_type,
        'will_return': will_return
    })
    
    data_dir = Path(__file__).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(data_dir / 'orders.csv', index=False)
    
    split = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    for train_idx, test_idx in split.split(df, df['will_return']):
        train_df = df.iloc[train_idx]
        test_df = df.iloc[test_idx]
        
    train_df.to_csv(data_dir / 'train.csv', index=False)
    test_df.to_csv(data_dir / 'test.csv', index=False)
    
    print("Summary Stats:")
    print(f"Total: {len(df)}")
    print(f"Train: {len(train_df)}")
    print(f"Test:  {len(test_df)}")
    print(f"Return Rate (total): {df['will_return'].mean():.4f}")

if __name__ == '__main__':
    generate_data()
