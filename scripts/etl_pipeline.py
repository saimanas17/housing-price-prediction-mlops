import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import os
from datetime import datetime
import json

def run_etl():
    print("=" * 60)
    print("House Price Prediction - ETL Pipeline")
    print("=" * 60)
    
    # 1. Load raw data
    print("\n[1/6] Loading raw data...")
    df = pd.read_csv('data/raw/train.csv')
    print(f"   Loaded {len(df)} records with {df.shape[1]} columns")
    print(f"   Target variable: SalePrice")
    
    # 2. Data Quality Checks
    print("\n[2/6] Running data quality checks...")
    missing_counts = df.isnull().sum()
    cols_with_missing = missing_counts[missing_counts > 0]
    print(f"   Columns with missing values: {len(cols_with_missing)}")
    print(f"   Total missing values: {df.isnull().sum().sum()}")
    
    # 3. Feature Selection - Keep only numeric + important categorical
    print("\n[3/6] Feature selection...")
    
    # Select important features (you can expand this list)
    selected_features = [
        'LotArea', 'OverallQual', 'OverallCond', 'YearBuilt', 'YearRemodAdd',
        'TotalBsmtSF', '1stFlrSF', '2ndFlrSF', 'GrLivArea', 
        'FullBath', 'HalfBath', 'BedroomAbvGr', 'TotRmsAbvGrd',
        'Fireplaces', 'GarageCars', 'GarageArea', 'WoodDeckSF',
        'OpenPorchSF', 'PoolArea', 'YrSold', 'MoSold'
    ]
    
    # Add target
    df_selected = df[selected_features + ['SalePrice']].copy()
    print(f"   Selected {len(selected_features)} features")
    
    # 4. Handle Missing Values
    print("\n[4/6] Handling missing values...")
    # Fill numeric missing values with median
    for col in df_selected.columns:
        if df_selected[col].isnull().sum() > 0:
            df_selected[col].fillna(df_selected[col].median(), inplace=True)
    print(f"   Missing values after handling: {df_selected.isnull().sum().sum()}")
    
    # 5. Feature Engineering
    print("\n[5/6] Feature engineering...")
    df_selected['HouseAge'] = df_selected['YrSold'] - df_selected['YearBuilt']
    df_selected['RemodAge'] = df_selected['YrSold'] - df_selected['YearRemodAdd']
    df_selected['TotalSF'] = df_selected['TotalBsmtSF'] + df_selected['1stFlrSF'] + df_selected['2ndFlrSF']
    df_selected['TotalBath'] = df_selected['FullBath'] + 0.5 * df_selected['HalfBath']
    df_selected['PricePerSqFt'] = df_selected['SalePrice'] / df_selected['GrLivArea']
    
    print(f"   Created 5 new features")
    print(f"   Total features: {len(df_selected.columns) - 1}")  # Exclude target
    
    # 6. Train/Validation/Test Split
    print("\n[6/6] Splitting data...")
    # First split: 80% train+val, 20% test
    train_val_df, test_df = train_test_split(df_selected, test_size=0.2, random_state=42)
    # Second split: 75% train, 25% val (of the 80%)
    train_df, val_df = train_test_split(train_val_df, test_size=0.25, random_state=42)
    
    print(f"   Training set: {len(train_df)} records ({len(train_df)/len(df_selected)*100:.1f}%)")
    print(f"   Validation set: {len(val_df)} records ({len(val_df)/len(df_selected)*100:.1f}%)")
    print(f"   Test set: {len(test_df)} records ({len(test_df)/len(df_selected)*100:.1f}%)")
    
    # 7. Save processed data
    print("\nSaving processed data...")
    os.makedirs('data/processed', exist_ok=True)
    
    train_df.to_csv('data/processed/train.csv', index=False)
    val_df.to_csv('data/processed/val.csv', index=False)
    test_df.to_csv('data/processed/test.csv', index=False)
    
    # Save metadata
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'total_records': len(df_selected),
        'train_records': len(train_df),
        'val_records': len(val_df),
        'test_records': len(test_df),
        'features': [col for col in df_selected.columns if col != 'SalePrice'],
        'target': 'SalePrice',
        'price_stats': {
            'mean': float(df_selected['SalePrice'].mean()),
            'median': float(df_selected['SalePrice'].median()),
            'min': float(df_selected['SalePrice'].min()),
            'max': float(df_selected['SalePrice'].max())
        }
    }
    
    with open('data/processed/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 60)
    print("ETL Pipeline Completed Successfully!")
    print("=" * 60)
    print(f"\nOutput files:")
    print(f"  - data/processed/train.csv ({len(train_df)} rows)")
    print(f"  - data/processed/val.csv ({len(val_df)} rows)")
    print(f"  - data/processed/test.csv ({len(test_df)} rows)")
    print(f"  - data/processed/metadata.json")
    print(f"\nPrice Range: ${metadata['price_stats']['min']:,.0f} - ${metadata['price_stats']['max']:,.0f}")
    print(f"Average Price: ${metadata['price_stats']['mean']:,.0f}")
    
    return metadata

if __name__ == "__main__":
    run_etl()
