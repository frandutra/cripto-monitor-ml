
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

def train_model():
    # 1. Load Data
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'raw_btc_data.csv')
    print(f"Loading data from {data_path}...")
    
    if not os.path.exists(data_path):
        print("Data file not found!")
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

    # 2. Feature Engineering
    # Calculate MA_20 if not present
    if 'MA_20' not in df.columns:
        df['MA_20'] = df['Close'].rolling(window=20).mean()
    
    # RELATIVE FEATURES (Percentage based) - Critical for handling price drift!
    # 1. 1-minute Return (Momentum)
    df['Returns_1m'] = df['Close'].pct_change(1)
    
    # 2. 2-minute Return (Lagged Momentum)
    df['Returns_2m'] = df['Close'].pct_change(2)
    
    # 3. Distance from Moving Average (Trend Strength/Reversion)
    # (Price - MA) / MA
    df['Dist_MA_20'] = (df['Close'] - df['MA_20']) / df['MA_20']
    
    # Target: 1 if Close(t+1) > Close(t)
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    
    # Drop NaNs created by rolling/shifting
    df_ml = df.dropna()
    
    print(f"Data shape after cleaning: {df_ml.shape}")
    print("Class Balance:")
    print(df_ml['Target'].value_counts(normalize=True))
    
    # Update feature list to use ONLY relative metrics
    features = ['Returns_1m', 'Returns_2m', 'Dist_MA_20']
    X = df_ml[features]
    y = df_ml['Target']
    
    # 3. Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    # 4. Train
    print("Training Random Forest...")
    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10, min_samples_leaf=5) 
    # Added constraints to prevent overfitting/memorization
    
    model.fit(X_train, y_train)
    
    # 5. Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    print("\nSample Probabilities (First 10 of Test Set):")
    print(y_proba[:10])
    
    # 6. Save
    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models', 'crypto_model.pkl')
    joblib.dump({'model': model, 'features': features}, model_path)
    print(f"\nModel saved to {model_path}")

if __name__ == "__main__":
    train_model()
