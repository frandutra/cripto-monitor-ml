
import joblib
import os
import pandas as pd
import numpy as np

def inspect_model():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    model_path = os.path.join(project_root, 'models', 'crypto_model.pkl')
    if not os.path.exists(model_path):
        print(f"Model file not found at {model_path}")
        return

    data_pack = joblib.load(model_path)
    print("Keys in data_pack:", data_pack.keys())
    
    if 'model' in data_pack:
        print("\nModel Object:", data_pack['model'])
    
    if 'features' in data_pack:
        print("\nFeatures required:", data_pack['features'])
        
    # Create dummy data to test variance
    if 'features' in data_pack and 'model' in data_pack:
        features = data_pack['features']
        print(f"\nTesting inference with random data specific to {len(features)} features...")
        
        # Batch test: Generate 100 realistic samples (Random Walks)
        n_samples = 100
        
        # Base price matching the training data (88k-93k)
        base_price = 90000
        
        # Generate varied scenarios
        # Scenario 1: Uptrend (Close > Lag1 > Lag2)
        # Scenario 2: Downtrend (Close < Lag1 < Lag2)
        # Scenario 3: flat
        
        data = []
        for _ in range(n_samples):
            # Random trend direction
            trend = np.random.choice([-1, 0, 1]) 
            step = np.random.uniform(50, 500)
            
            p_lag2 = base_price + np.random.uniform(-1000, 1000)
            p_lag1 = p_lag2 + (step * trend) + np.random.normal(0, 50)
            p_close = p_lag1 + (step * trend) + np.random.normal(0, 50)
            
            # MA_20: roughly near price, maybe lagging
            ma_20 = p_close - (step * trend * 10) # Simple proxy for lag
            
            data.append([p_close, ma_20, p_lag1, p_lag2])
            
        dummy_df = pd.DataFrame(data, columns=['Close', 'MA_20', 'Close_Lag1', 'Close_Lag2'])
        
        # Ensure column order matches model features
        dummy_df = dummy_df[features]
        
        probs = data_pack['model'].predict_proba(dummy_df)
        
        # Check variance
        unique_probs = np.unique(probs, axis=0)
        print(f"\nTested {n_samples} samples.")
        print(f"Unique probability outputs found: {len(unique_probs)}")
        print("First 5 outputs:")
        print(probs[:5])
        
        if len(unique_probs) == 1:
            print("\nWARNING: Model is outputting identical probabilities for all inputs.")
        else:
            print(f"\nModel is responsive to input changes. (Found {len(unique_probs)} unique scores)")
        
    if 'target' in data_pack:
         print("\nTarget:", data_pack['target'])

if __name__ == "__main__":
    inspect_model()
