
import pandas as pd

def calculate_features(df):
    """
    Centralized feature engineering logic to ensure consistency 
    between Training, Inference (App), and Backtesting.
    """
    df = df.copy()
    
    # Ensure numeric types
    cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # --- INDICATORS ---
    # 1. Moving Average 20
    df['MA_20'] = df['Close'].rolling(window=20).mean()
    
    # 2. Relative Features (Percentage based)
    # 1-period Return (Momentum)
    df['Returns_1m'] = df['Close'].pct_change(1)
    
    # 2-period Return (Lagged Momentum)
    df['Returns_2m'] = df['Close'].pct_change(2)
    
    # Distance from Moving Average (Trend Strength/Reversion)
    df['Dist_MA_20'] = (df['Close'] - df['MA_20']) / df['MA_20']
    
    # --- NEW INDICATORS ---
    # 3. RSI (Relative Strength Index) - 14 periods
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    # 4. Bollinger Bands (Volatility)
    # Already have MA_20. Need Std Dev.
    std_20 = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['MA_20'] + (std_20 * 2)
    df['BB_Lower'] = df['MA_20'] - (std_20 * 2)
    
    # Feature: Position within Bands (0 = Lower, 1 = Upper, >1 Overbought, <0 Oversold)
    # Avoid division by zero
    bb_width = (df['BB_Upper'] - df['BB_Lower']).replace(0, 0.000001)
    df['BB_Position'] = (df['Close'] - df['BB_Lower']) / bb_width
    
    # Handle infinite or NaN values created by calculations
    df.replace([float('inf'), float('-inf')], 0, inplace=True)
    
    return df
