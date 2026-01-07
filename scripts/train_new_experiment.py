import os
os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:30000"

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import mlflow
import mlflow.sklearn

def load_data():
    train_df = pd.read_csv('data/processed/train.csv')
    val_df = pd.read_csv('data/processed/val.csv')
    test_df = pd.read_csv('data/processed/test.csv')
    
    X_train = train_df.drop('SalePrice', axis=1)
    y_train = train_df['SalePrice']
    X_val = val_df.drop('SalePrice', axis=1)
    y_val = val_df['SalePrice']
    X_test = test_df.drop('SalePrice', axis=1)
    y_test = test_df['SalePrice']
    
    return X_train, y_train, X_val, y_val, X_test, y_test

def evaluate_model(model, X, y, dataset_name="Dataset"):
    y_pred = model.predict(X)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    mae = mean_absolute_error(y, y_pred)
    r2 = r2_score(y, y_pred)
    mape = np.mean(np.abs((y - y_pred) / y)) * 100
    
    print(f"{dataset_name} - RMSE: ${rmse:,.2f}, MAE: ${mae:,.2f}, R²: {r2:.4f}, MAPE: {mape:.2f}%")
    
    return {
        f'{dataset_name}_rmse': rmse,
        f'{dataset_name}_mae': mae,
        f'{dataset_name}_r2': r2,
        f'{dataset_name}_mape': mape
    }

def main():
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:30000"))
    
    # CREATE NEW EXPERIMENT (this will get mlflow-artifacts:/ root)
    try:
        exp_id = mlflow.create_experiment("house-price-mlflow-artifacts")
        print(f"✓ Created new experiment with ID: {exp_id}")
    except:
        print("Experiment already exists, using it...")
    
    mlflow.set_experiment("house-price-mlflow-artifacts")
    
    print("="*60)
    print("MLflow Training with HTTP Artifacts")
    print("="*60)
    print(f"MLflow Version: {mlflow.__version__}")
    print(f"Tracking URI: {mlflow.get_tracking_uri()}")
    
    X_train, y_train, X_val, y_val, X_test, y_test = load_data()
    print(f"\nData: Train={X_train.shape}, Val={X_val.shape}, Test={X_test.shape}")
    
    # Train Baseline
    print("\n" + "="*60)
    print("Training Baseline: Linear Regression")
    print("="*60)
    
    with mlflow.start_run(run_name="linear_regression_baseline"):
        # Check artifact URI FIRST
        artifact_uri = mlflow.get_artifact_uri()
        print(f"\n🔍 Artifact URI: {artifact_uri}")
        
        if not artifact_uri.startswith("mlflow-artifacts:/"):
            print("❌ ERROR: Artifact URI is not mlflow-artifacts://")
            print("   Server config issue - check --default-artifact-root")
            return
        
        print("✓ Artifact URI is correct! (mlflow-artifacts:/)")
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        mlflow.log_param("model_type", "LinearRegression")
        train_metrics = evaluate_model(model, X_train, y_train, "train")
        val_metrics = evaluate_model(model, X_val, y_val, "val")
        mlflow.log_metrics({**train_metrics, **val_metrics})
        
        print("\nLogging model artifact via HTTP...")
        mlflow.sklearn.log_model(model, "model")
        print("✓ Baseline model logged successfully!")
        baseline_run_id = mlflow.active_run().info.run_id
    
    # Train Advanced
    print("\n" + "="*60)
    print("Training Advanced: Gradient Boosting")
    print("="*60)
    
    params = {
        'n_estimators': 100,
        'learning_rate': 0.1,
        'max_depth': 5,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'random_state': 42
    }
    
    with mlflow.start_run(run_name="gradient_boosting"):
        artifact_uri = mlflow.get_artifact_uri()
        print(f"\n🔍 Artifact URI: {artifact_uri}")
        
        model = GradientBoostingRegressor(**params)
        model.fit(X_train, y_train)
        
        mlflow.log_param("model_type", "GradientBoostingRegressor")
        mlflow.log_params(params)
        
        train_metrics = evaluate_model(model, X_train, y_train, "train")
        val_metrics = evaluate_model(model, X_val, y_val, "val")
        test_metrics = evaluate_model(model, X_test, y_test, "test")
        mlflow.log_metrics({**train_metrics, **val_metrics, **test_metrics})
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 10 Features:")
        print(feature_importance.head(10).to_string(index=False))
        
        print("\nLogging model artifact via HTTP...")
        mlflow.sklearn.log_model(model, "model")
        print("✓ Advanced model logged successfully!")
        advanced_run_id = mlflow.active_run().info.run_id
    
    print("\n" + "="*60)
    print("🎉 TRAINING COMPLETE - ARTIFACTS IN MLFLOW!")
    print("="*60)
    print(f"✓ Baseline Run: {baseline_run_id}")
    print(f"✓ Advanced Run: {advanced_run_id}")
    print(f"✓ Test R²: {test_metrics['test_r2']:.4f}")
    print(f"\n👉 View in MLflow UI: http://<your-ip>:30000")
    print(f"👉 Experiment: house-price-mlflow-artifacts")

if __name__ == "__main__":
    main()
