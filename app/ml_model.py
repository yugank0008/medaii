import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib
import os
from typing import Dict, Any

class DiseasePredictor:
    def __init__(self):
        self.model = None
        self.model_path = "trained_models/diabetes_model.joblib"
        
    def train_diabetes_model(self):
        """Train a sample diabetes prediction model"""
        # Load sample data (you should replace this with real data)
        # For demo purposes, we'll create synthetic data
        np.random.seed(42)
        n_samples = 1000
        
        data = {
            'age': np.random.randint(20, 80, n_samples),
            'bmi': np.random.uniform(18, 40, n_samples),
            'glucose': np.random.uniform(70, 200, n_samples),
            'blood_pressure': np.random.uniform(60, 140, n_samples),
            'pregnancies': np.random.randint(0, 10, n_samples),
            'skin_thickness': np.random.uniform(7, 50, n_samples),
            'insulin': np.random.uniform(0, 300, n_samples),
            'diabetes_pedigree': np.random.uniform(0.08, 2.5, n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Create synthetic target based on some rules
        conditions = (
            (df['glucose'] > 140) |
            (df['bmi'] > 30) |
            (df['age'] > 45) |
            (df['blood_pressure'] > 130)
        )
        
        df['diabetes'] = np.where(conditions, 1, 0)
        
        # Add some noise
        noise = np.random.choice([0, 1], size=n_samples, p=[0.8, 0.2])
        df['diabetes'] = np.where(noise == 1, 1 - df['diabetes'], df['diabetes'])
        
        X = df.drop('diabetes', axis=1)
        y = df['diabetes']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Model accuracy: {accuracy:.2f}")
        
        # Save model
        os.makedirs("trained_models", exist_ok=True)
        joblib.dump(self.model, self.model_path)
        
        return accuracy
    
    def load_model(self):
        """Load trained model"""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
        else:
            print("Training new model...")
            self.train_diabetes_model()
    
    def predict_diabetes_risk(self, data: Dict[str, Any]) -> float:
        """Predict diabetes risk based on input data"""
        if self.model is None:
            self.load_model()
        
        # Prepare input features
        features = [
            data.get('age', 30),
            data.get('bmi', 25),
            data.get('glucose', 100),
            data.get('blood_pressure', 120),
            data.get('pregnancies', 0),
            data.get('skin_thickness', 20),
            data.get('insulin', 80),
            data.get('diabetes_pedigree', 0.5)
        ]
        
        # Predict probability
        risk_prob = self.model.predict_proba([features])[0][1]
        return float(risk_prob)

# Initialize predictor
predictor = DiseasePredictor()
