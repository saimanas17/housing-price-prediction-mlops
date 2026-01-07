import bentoml
import mlflow
import pandas as pd
import os

# Expected features in training order
EXPECTED_FEATURES = [
    'LotArea', 'OverallQual', 'OverallCond', 'YearBuilt', 'YearRemodAdd',
    'TotalBsmtSF', '1stFlrSF', '2ndFlrSF', 'GrLivArea', 
    'FullBath', 'HalfBath', 'BedroomAbvGr', 'TotRmsAbvGrd',
    'Fireplaces', 'GarageCars', 'GarageArea', 'WoodDeckSF',
    'OpenPorchSF', 'PoolArea', 'YrSold', 'MoSold',
    'HouseAge', 'RemodAge', 'TotalSF', 'TotalBath', 'PricePerSqFt'
]

@bentoml.service(
    name="housing-predictor",
    resources={"cpu": "1"},
)
class HousingPredictor:
    
    def __init__(self):
        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:30000")
        mlflow.set_tracking_uri(mlflow_uri)
        
        print(f"Loading model from MLflow: {mlflow_uri}")
        self.model = mlflow.pyfunc.load_model("models:/housing model@production")
        self.feature_names = EXPECTED_FEATURES
        
        print("✓ Model loaded successfully")
    
    @bentoml.api
    def predict(self, input_data: dict) -> dict:
        """Predict house price"""
        try:
            data = input_data.copy()
            
            # Handle field naming
            if 'FirstFlrSF' in data:
                data['1stFlrSF'] = data.pop('FirstFlrSF')
            if 'SecondFlrSF' in data:
                data['2ndFlrSF'] = data.pop('SecondFlrSF')
            
            df = pd.DataFrame([data])
            
            # Check missing
            missing = set(self.feature_names) - set(df.columns)
            if missing:
                return {"status": "error", "message": f"Missing: {list(missing)}"}
            
            # Reorder
            df = df[self.feature_names]
            
            # Predict
            prediction = self.model.predict(df)
            
            return {
                "predicted_price": float(prediction[0]),
                "predicted_price_formatted": f"${prediction[0]:,.2f}",
                "status": "success"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @bentoml.api
    def health(self) -> dict:
        return {"status": "healthy"}
