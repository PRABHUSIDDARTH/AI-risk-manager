import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from features import build_preprocessor, FEATURE_COLS, LABEL_COL, NUMERIC_COLS, BOOL_COLS, CATEGORIC_COLS

def train_model():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data'
    ml_dir = base_dir / 'ml'
    ml_dir.mkdir(parents=True, exist_ok=True)
    
    # Load ONLY data/train.csv (never touch test.csv during training)
    train_path = data_dir / 'train.csv'
    df_train = pd.read_csv(train_path)
    
    X = df_train[FEATURE_COLS]
    y = df_train[LABEL_COL]
    
    pipeline = Pipeline([
        ('preprocessor', build_preprocessor()),
        ('clf', GradientBoostingClassifier(n_estimators=300, learning_rate=0.05, max_depth=4, subsample=0.8, random_state=42))
    ])
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(pipeline, X, y, cv=cv, scoring='roc_auc')
    print(f"5-fold CV Mean ROC-AUC: {np.mean(scores):.4f}")
    
    pipeline.fit(X, y)
    
    model_path = ml_dir / 'model.pkl'
    joblib.dump(pipeline, model_path)
    
    model_version = 'gbc-v1'
    with open(ml_dir / 'model_version.txt', 'w') as f:
        f.write(model_version)
        
    print(f"Model saved to {model_path} (Version: {model_version})")
    
    preprocessor = pipeline.named_steps['preprocessor']
    clf = pipeline.named_steps['clf']
    
    cat_features = preprocessor.named_transformers_['cat'].get_feature_names_out(CATEGORIC_COLS)
    all_features = NUMERIC_COLS + list(cat_features) + BOOL_COLS
    
    importances = clf.feature_importances_
    feat_imp = pd.Series(importances, index=all_features).sort_values(ascending=False)
    print("\nTop 10 Feature Importances:")
    print(feat_imp.head(10))

if __name__ == '__main__':
    train_model()
