import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from features import FEATURE_COLS, LABEL_COL

def evaluate_model():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data'
    ml_dir = base_dir / 'ml'
    
    # Load ONLY data/test.csv for evaluation (held-out set)
    test_path = data_dir / 'test.csv'
    df_test = pd.read_csv(test_path)
    
    model_path = ml_dir / 'model.pkl'
    pipeline = joblib.load(model_path)
    
    X_test = df_test[FEATURE_COLS]
    y_test = df_test[LABEL_COL]
    
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)
    
    print(f"Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"Recall:    {recall_score(y_test, y_pred):.4f}")
    print(f"F1 Score:  {f1_score(y_test, y_pred):.4f}")
    print(f"ROC-AUC:   {roc_auc_score(y_test, y_prob):.4f}")
    
    cm = confusion_matrix(y_test, y_pred)
    print("\nConfusion Matrix (Threshold=0.5):")
    print(f"TN: {cm[0,0]:4d} | FP: {cm[0,1]:4d}")
    print(f"FN: {cm[1,0]:4d} | TP: {cm[1,1]:4d}")
    
    print("\nCost Analysis (FP Cost=$2.0, FN Cost=$15.0):")
    print(f"{'Threshold':<10} {'FP Count':<10} {'FN Count':<10} {'Expected Cost'}")
    
    FP_COST = 2.0
    FN_COST = 15.0
    thresholds = [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
    
    best_cost = float('inf')
    best_thresh = None
    
    for th in thresholds:
        pred_th = (y_prob >= th).astype(int)
        cm_th = confusion_matrix(y_test, pred_th)
        fp_count = cm_th[0, 1]
        fn_count = cm_th[1, 0]
        cost = fp_count * FP_COST + fn_count * FN_COST
        print(f"{th:<10.2f} {fp_count:<10d} {fn_count:<10d} ${cost:.2f}")
        
        if cost < best_cost:
            best_cost = cost
            best_thresh = th
            
    print(f"\nRecommended optimal threshold: {best_thresh:.2f} (Expected Cost: ${best_cost:.2f})")

if __name__ == '__main__':
    evaluate_model()
