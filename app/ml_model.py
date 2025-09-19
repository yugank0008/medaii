import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib
import os
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class DiseasePredictor:
    def __init__(self):
        self.model = None
        # Use absolute path for deployment
        base_dir = Path(__file__).parent.parent
        self.model_path = os.path.join(base_dir, "trained_models", "diabetes_model.joblib")
        self.ensure_directories()
        
    def ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
    def train_diabetes_model(self):
        """Train a sample diabetes prediction model"""
        try:
            logger.info("Training diabetes prediction model...")
            
            # Create synthetic data for demonstration
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
            
            # Create synthetic target
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
            
            # Save model
            joblib.dump(self.model, self.model_path)
            
            logger.info(f"Model trained successfully with accuracy: {accuracy:.2f}")
            return accuracy
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            raise
    
    def load_model(self):
        """Load trained model"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                logger.info("Model loaded successfully")
            else:
                logger.warning("Model file not found, training new model...")
                self.train_diabetes_model()
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            # Create a fallback model
            self._create_fallback_model()
    
    def _create_fallback_model(self):
        """Create a simple fallback model"""
        try:
            logger.info("Creating fallback model...")
            self.model = RandomForestClassifier(n_estimators=10, random_state=42)
            # Train on minimal data
            X = np.random.rand(10, 8)
            y = np.random.randint(0, 2, 10)
            self.model.fit(X, y)
            joblib.dump(self.model, self.model_path)
            logger.info("Fallback model created")
        except Exception as e:
            logger.error(f"Fallback model creation failed: {e}")
            self.model = None
    
    def predict_diabetes_risk(self, data: Dict[str, Any]) -> float:
        """Predict diabetes risk based on input data"""
        if self.model is None:
            self.load_model()
            
        if self.model is None:
            # Return a default risk if model is not available
            return 0.3
        
        try:
            # Prepare input features with defaults
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
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            # Return a safe default value
            return 0.3

# Initialize predictor
predictor = DiseasePredictor()
