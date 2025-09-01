#!/usr/bin/env python3
"""
ML Preprocessing Script for Comprehensive Tracking Data
Prepares data from comprehensive_tracking.jsonl for Grokkeeper's ML models
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import sys

def load_tracking_data(filepath='/root/HydraX-v2/logs/comprehensive_tracking.jsonl'):
    """Load JSONL tracking data into DataFrame"""
    data = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return pd.DataFrame()
    
    return pd.DataFrame(data)

def preprocess_for_ml(df):
    """Preprocess data for ML models"""
    
    if df.empty:
        print("❌ No data to preprocess")
        return df
    
    # Handle missing values
    numeric_cols = ['confidence', 'entry_price', 'sl_price', 'tp_price', 
                   'lot_size', 'pips', 'rsi', 'volume', 'shield_score',
                   'risk_pct', 'balance', 'equity', 'expectancy', 'ml_score']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col].fillna(df[col].median() if not df[col].isna().all() else 0, inplace=True)
    
    # Convert categorical to numeric
    if 'direction' in df.columns:
        df['direction_encoded'] = df['direction'].map({'BUY': 1, 'SELL': -1}).fillna(0)
    
    if 'pattern' in df.columns:
        df['pattern_encoded'] = pd.Categorical(df['pattern']).codes
    
    if 'session' in df.columns:
        session_map = {'ASIAN': 0, 'LONDON': 1, 'NEWYORK': 2, 'SYDNEY': 3, 'OVERLAP': 4}
        df['session_encoded'] = df['session'].map(session_map).fillna(0)
    
    # Convert win/loss to binary
    if 'win' in df.columns:
        df['win_binary'] = df['win'].astype(float).fillna(0.5)  # 0.5 for unknown outcomes
    
    # Calculate derived features
    if 'entry_price' in df.columns and 'sl_price' in df.columns:
        df['risk_pips'] = abs(df['entry_price'] - df['sl_price']) * 10000
    
    if 'tp_price' in df.columns and 'entry_price' in df.columns:
        df['reward_pips'] = abs(df['tp_price'] - df['entry_price']) * 10000
    
    if 'risk_pips' in df.columns and 'reward_pips' in df.columns:
        df['risk_reward_ratio'] = df['reward_pips'] / df['risk_pips'].replace(0, 1)
    
    # Handle timestamps
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
    
    # Remove NaN and infinity values
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    # Select features for ML
    ml_features = [
        'confidence', 'shield_score', 'risk_reward_ratio',
        'direction_encoded', 'pattern_encoded', 'session_encoded',
        'hour', 'day_of_week', 'rsi', 'volume',
        'win_binary'  # Target variable
    ]
    
    available_features = [f for f in ml_features if f in df.columns]
    ml_df = df[available_features].copy()
    
    # Final cleanup
    ml_df.dropna(inplace=True)
    
    return ml_df

def generate_ml_report(df):
    """Generate ML-ready report"""
    
    print("📊 ML Preprocessing Report")
    print("=" * 50)
    print(f"Total records: {len(df)}")
    
    if 'win_binary' in df.columns:
        win_rate = df['win_binary'].mean()
        print(f"Win rate: {win_rate:.2%}")
    
    if 'pattern_encoded' in df.columns:
        print(f"Unique patterns: {df['pattern_encoded'].nunique()}")
    
    if 'confidence' in df.columns:
        print(f"Avg confidence: {df['confidence'].mean():.1f}")
    
    if 'shield_score' in df.columns:
        print(f"Avg shield score: {df['shield_score'].mean():.1f}")
    
    print("\nFeature statistics:")
    print(df.describe())
    
    # Save preprocessed data
    output_file = '/root/HydraX-v2/logs/ml_preprocessed_data.csv'
    df.to_csv(output_file, index=False)
    print(f"\n✅ Preprocessed data saved to: {output_file}")
    
    return df

def main():
    """Main preprocessing pipeline"""
    print("🤖 Starting ML preprocessing...")
    
    # Load data
    df = load_tracking_data()
    
    if df.empty:
        print("❌ No data found to preprocess")
        return
    
    print(f"✅ Loaded {len(df)} records")
    
    # Preprocess
    ml_df = preprocess_for_ml(df)
    
    # Generate report
    generate_ml_report(ml_df)
    
    print("\n✅ ML preprocessing complete!")
    
    return ml_df

if __name__ == "__main__":
    main()
