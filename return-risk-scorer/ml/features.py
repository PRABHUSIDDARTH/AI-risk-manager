import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

FEATURE_COLS = [
    'order_value', 'num_items', 'category', 'payment_method',
    'customer_return_rate', 'days_to_deliver', 'seller_rating',
    'is_first_order', 'discount_pct', 'pincode_return_rate',
    'hour_of_order', 'device_type'
]
NUMERIC_COLS = ['order_value','num_items','customer_return_rate','days_to_deliver',
                'seller_rating','discount_pct','pincode_return_rate','hour_of_order']
CATEGORIC_COLS = ['category','payment_method','device_type']
BOOL_COLS = ['is_first_order']
LABEL_COL = 'will_return'

def build_preprocessor():
    """Returns a ColumnTransformer for the feature set."""
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, NUMERIC_COLS),
            ('cat', categorical_transformer, CATEGORIC_COLS),
            ('bool', 'passthrough', BOOL_COLS),
        ]
    )
    return preprocessor

def order_dict_to_df(order: dict) -> pd.DataFrame:
    """Converts a single order dict to a 1-row DataFrame."""
    row = {col: [order[col]] for col in FEATURE_COLS}
    df = pd.DataFrame(row)
    df['is_first_order'] = df['is_first_order'].astype(int)
    return df
