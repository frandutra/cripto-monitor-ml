
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os
from features import calculate_features

def train_model(ticker="BTC-USD", interval="5m"):
    # 1. Load Data
    safe_ticker = ticker.replace("-", "_")
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', f'raw_{safe_ticker}_data.csv')
    print(f"Loading data from {data_path}...")
    
    if not os.path.exists(data_path):
        print(f"Data file not found at {data_path}!")
        return

    # Load data
    # The CSV has 3 header rows:
    # 1: Price,Close,High,Low,Open,Volume
    # 2: Ticker,BTC-USD,BTC-USD...
    # 3: Datetime,,,,,
    # We want to skip 2 and 3, or better yet, read properly.
    
    # Reading with header=0 reads line 1.
    df = pd.read_csv(data_path, header=0)
    
    # Drop the first two rows (Ticker and Datetime placeholders) which are now rows 0 and 1 in the DF
    df = df.iloc[2:]
    
    # Rename the index column (first column) to Datetime
    df.rename(columns={'Price': 'Datetime'}, inplace=True)
    
    # Set index
    df.set_index('Datetime', inplace=True)
    df.index = pd.to_datetime(df.index)
    
    # Convert numeric columns
    numeric_cols = ['Close', 'High', 'Low', 'Open', 'Volume']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Sort
    df = df.sort_index()

    # 2. Feature Engineering (Centralized)
    df = calculate_features(df)
    
    # Target: 1 if Close(t+1) > Close(t)
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    
    # Drop NaNs created by rolling/shifting
    df_ml = df.dropna()
    
    if df_ml.empty:
        print("Not enough data to train model.")
        return

    print(f"Data shape after cleaning: {df_ml.shape}")
    print("Class Balance:")
    print(df_ml['Target'].value_counts(normalize=True))
    
    # Update feature list to use ONLY relative metrics
    features = ['Returns_1m', 'Returns_2m', 'Dist_MA_20', 'RSI_14', 'BB_Position']
    X = df_ml[features]
    y = df_ml['Target']
    
    # 3. Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    # 4. Train
    print(f"Training Random Forest for {ticker}...")
    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10, min_samples_leaf=5) 
    # Added constraints to prevent overfitting/memorization
    
    model.fit(X_train, y_train)
    
    # --- FEATURE IMPORTANCE (Data Science) ---
    # Extraemos qué variables influyen más en la decisión del modelo
    importances = model.feature_importances_
    feature_imp_df = pd.DataFrame({
        'Feature': features,
        'Importance': importances
    }).sort_values(by='Importance', ascending=False)
    
    print("\n[INFO] Feature Importance (Top drivers):")
    print(feature_imp_df)
    
    # 5. Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] # Probability for class 1 (Sube)
    
    from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred),
        'roc_auc': roc_auc_score(y_test, y_proba),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist() # Convert to list for serialization
    }
    
    print(f"Accuracy: {metrics['accuracy']:.2f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # 6. Save
    model_filename = f'crypto_model_{safe_ticker}.pkl'
    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models', model_filename)
    
    # Guardamos también los artefactos para visualizar en la App
    joblib.dump({
        'model': model, 
        'features': features, 
        'interval': interval, 
        'ticker': ticker,
        'feature_importance': feature_imp_df,
        'metrics': metrics # Nuevo artefacto para estadísticas
    }, model_path)
    
    print(f"\nModel saved to {model_path} with training interval: {interval}")

if __name__ == "__main__":
    train_model()
