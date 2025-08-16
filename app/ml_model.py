import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score
)
from typing import Tuple, Dict, Any
import logging
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Try to import xgboost, use fallback if not available
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("Warning: XGBoost not available. Using RandomForest as default model.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhishingDetectionModel:
    """
    Machine Learning model for phishing URL detection
    """
    
    def __init__(self, model_type: str = 'xgboost'):
        """
        Initialize the model
        
        Args:
            model_type: Type of model to use ('xgboost', 'random_forest', 'logistic', 'svm', 'gradient_boost')
        """
        # If XGBoost is not available and user requested it, fall back to random_forest
        if model_type == 'xgboost' and not XGBOOST_AVAILABLE:
            print("XGBoost not available, falling back to Random Forest")
            model_type = 'random_forest'
        
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.is_trained = False
        
        # Initialize model based on type
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the specified model"""
        if self.model_type == 'xgboost':
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                eval_metric='logloss'
            )
        elif self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
        elif self.model_type == 'gradient_boost':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        elif self.model_type == 'logistic':
            self.model = LogisticRegression(
                random_state=42,
                max_iter=1000
            )
        elif self.model_type == 'svm':
            self.model = SVC(
                kernel='rbf',
                probability=True,
                random_state=42
            )
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for training/prediction
        
        Args:
            df: DataFrame with features and labels
            
        Returns:
            Tuple of (features, labels)
        """
        # Separate features and labels
        if 'label' in df.columns:
            X = df.drop(['label'], axis=1)
            y = df['label']
        else:
            X = df
            y = None
        
        # Store feature columns for later use
        if self.feature_columns is None:
            self.feature_columns = X.columns.tolist()
        
        # Ensure consistent column order
        X = X[self.feature_columns]
        
        # Handle missing values
        X = X.fillna(0)
        
        return X.values, y.values if y is not None else None
    
    def train(self, df: pd.DataFrame, test_size: float = 0.2, validate: bool = True) -> Dict[str, Any]:
        """
        Train the model on the provided dataset
        
        Args:
            df: DataFrame with features and labels
            test_size: Proportion of data to use for testing
            validate: Whether to perform validation
            
        Returns:
            Dictionary with training results and metrics
        """
        logger.info(f"Training {self.model_type} model...")
        
        # Prepare data
        X, y = self.prepare_data(df)
        
        if X.shape[0] == 0:
            raise ValueError("No data provided for training")
        
        logger.info(f"Dataset shape: {X.shape}")
        logger.info(f"Class distribution: {np.bincount(y)}")
        
        # Split data
        if validate:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
        else:
            X_train, X_test, y_train, y_test = X, None, y, None
        
        # Scale features (especially important for SVM and Logistic Regression)
        if self.model_type in ['svm', 'logistic']:
            X_train_scaled = self.scaler.fit_transform(X_train)
            if X_test is not None:
                X_test_scaled = self.scaler.transform(X_test)
        else:
            X_train_scaled = X_train
            X_test_scaled = X_test
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluate model
        results = {}
        
        # Training accuracy
        train_pred = self.model.predict(X_train_scaled)
        results['train_accuracy'] = accuracy_score(y_train, train_pred)
        
        if validate and X_test is not None:
            # Test predictions
            test_pred = self.model.predict(X_test_scaled)
            test_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
            
            # Calculate metrics
            results['test_accuracy'] = accuracy_score(y_test, test_pred)
            results['precision'] = precision_score(y_test, test_pred)
            results['recall'] = recall_score(y_test, test_pred)
            results['f1_score'] = f1_score(y_test, test_pred)
            results['auc_score'] = roc_auc_score(y_test, test_pred_proba)
            
            # Classification report
            results['classification_report'] = classification_report(y_test, test_pred)
            results['confusion_matrix'] = confusion_matrix(y_test, test_pred)
            
            logger.info(f"Model training complete!")
            logger.info(f"Test Accuracy: {results['test_accuracy']:.4f}")
            logger.info(f"F1 Score: {results['f1_score']:.4f}")
            logger.info(f"AUC Score: {results['auc_score']:.4f}")
        
        # Feature importance (if available)
        if hasattr(self.model, 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            results['feature_importance'] = importance_df
            logger.info("Top 10 most important features:")
            logger.info(importance_df.head(10))
        
        return results
    
    def cross_validate(self, df: pd.DataFrame, cv_folds: int = 5) -> Dict[str, float]:
        """
        Perform cross-validation on the dataset
        
        Args:
            df: DataFrame with features and labels
            cv_folds: Number of cross-validation folds
            
        Returns:
            Dictionary with cross-validation scores
        """
        logger.info(f"Performing {cv_folds}-fold cross-validation...")
        
        X, y = self.prepare_data(df)
        
        # Scale data if necessary
        if self.model_type in ['svm', 'logistic']:
            X = self.scaler.fit_transform(X)
        
        # Perform cross-validation
        cv_scores = cross_val_score(self.model, X, y, cv=cv_folds, scoring='accuracy')
        cv_precision = cross_val_score(self.model, X, y, cv=cv_folds, scoring='precision')
        cv_recall = cross_val_score(self.model, X, y, cv=cv_folds, scoring='recall')
        cv_f1 = cross_val_score(self.model, X, y, cv=cv_folds, scoring='f1')
        
        results = {
            'cv_accuracy_mean': cv_scores.mean(),
            'cv_accuracy_std': cv_scores.std(),
            'cv_precision_mean': cv_precision.mean(),
            'cv_precision_std': cv_precision.std(),
            'cv_recall_mean': cv_recall.mean(),
            'cv_recall_std': cv_recall.std(),
            'cv_f1_mean': cv_f1.mean(),
            'cv_f1_std': cv_f1.std()
        }
        
        logger.info(f"Cross-validation results:")
        logger.info(f"Accuracy: {results['cv_accuracy_mean']:.4f} ± {results['cv_accuracy_std']:.4f}")
        logger.info(f"F1 Score: {results['cv_f1_mean']:.4f} ± {results['cv_f1_std']:.4f}")
        
        return results
    
    def hyperparameter_tuning(self, df: pd.DataFrame, cv_folds: int = 3) -> Dict[str, Any]:
        """
        Perform hyperparameter tuning using GridSearchCV
        
        Args:
            df: DataFrame with features and labels
            cv_folds: Number of cross-validation folds for tuning
            
        Returns:
            Dictionary with best parameters and scores
        """
        logger.info("Starting hyperparameter tuning...")
        
        X, y = self.prepare_data(df)
        
        # Scale data if necessary
        if self.model_type in ['svm', 'logistic']:
            X = self.scaler.fit_transform(X)
        
        # Define parameter grids for different models
        param_grids = {
            'xgboost': {
                'n_estimators': [50, 100, 200],
                'max_depth': [3, 6, 9],
                'learning_rate': [0.01, 0.1, 0.2]
            },
            'random_forest': {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15, None],
                'min_samples_split': [2, 5, 10]
            },
            'gradient_boost': {
                'n_estimators': [50, 100, 200],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1, 0.2]
            },
            'logistic': {
                'C': [0.1, 1.0, 10.0],
                'penalty': ['l1', 'l2'],
                'solver': ['liblinear', 'saga']
            },
            'svm': {
                'C': [0.1, 1, 10],
                'gamma': ['scale', 'auto', 0.001, 0.01],
                'kernel': ['rbf', 'poly']
            }
        }
        
        if self.model_type not in param_grids:
            logger.warning(f"No parameter grid defined for {self.model_type}")
            return {}
        
        # Perform grid search
        grid_search = GridSearchCV(
            self.model,
            param_grids[self.model_type],
            cv=cv_folds,
            scoring='f1',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X, y)
        
        # Update model with best parameters
        self.model = grid_search.best_estimator_
        
        results = {
            'best_params': grid_search.best_params_,
            'best_score': grid_search.best_score_,
            'cv_results': grid_search.cv_results_
        }
        
        logger.info(f"Best parameters: {results['best_params']}")
        logger.info(f"Best cross-validation score: {results['best_score']:.4f}")
        
        return results
    
    def predict(self, url_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict if a single URL is phishing or not
        
        Args:
            url_features: Dictionary of extracted URL features
            
        Returns:
            Dictionary with prediction results
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Convert features to DataFrame
        df = pd.DataFrame([url_features])
        
        # Ensure all required features are present
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0
        
        # Order columns consistently
        df = df[self.feature_columns]
        
        # Handle missing values
        df = df.fillna(0)
        
        # Scale if necessary
        if self.model_type in ['svm', 'logistic']:
            X = self.scaler.transform(df.values)
        else:
            X = df.values
        
        # Make predictions
        prediction = self.model.predict(X)[0]
        prediction_proba = self.model.predict_proba(X)[0]
        
        results = {
            'is_phishing': bool(prediction),
            'phishing_probability': float(prediction_proba[1]),
            'legitimate_probability': float(prediction_proba[0]),
            'confidence': float(max(prediction_proba))
        }
        
        return results
    
    def predict_batch(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predict for multiple URLs
        
        Args:
            df: DataFrame with URL features
            
        Returns:
            Array of predictions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        X, _ = self.prepare_data(df)
        
        # Scale if necessary
        if self.model_type in ['svm', 'logistic']:
            X = self.scaler.transform(X)
        
        return self.model.predict(X)
    
    def save_model(self, filepath: str):
        """
        Save the trained model to disk
        
        Args:
            filepath: Path to save the model
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'model_type': self.model_type,
            'is_trained': self.is_trained
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """
        Load a trained model from disk
        
        Args:
            filepath: Path to the saved model
        """
        if not Path(filepath).exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_columns = model_data['feature_columns']
        self.model_type = model_data['model_type']
        self.is_trained = model_data['is_trained']
        
        logger.info(f"Model loaded from {filepath}")


class ModelEvaluator:
    """
    Class for comprehensive model evaluation and comparison
    """
    
    @staticmethod
    def compare_models(df: pd.DataFrame, model_types: list = None) -> pd.DataFrame:
        """
        Compare multiple model types on the same dataset
        
        Args:
            df: Dataset with features and labels
            model_types: List of model types to compare
            
        Returns:
            DataFrame with comparison results
        """
        if model_types is None:
            model_types = ['random_forest', 'gradient_boost', 'logistic']
            if XGBOOST_AVAILABLE:
                model_types.insert(0, 'xgboost')  # XGBoost first if available
        
        logger.info("Comparing multiple models...")
        
        results = []
        
        for model_type in model_types:
            try:
                logger.info(f"Training {model_type} model...")
                
                # Initialize and train model
                model = PhishingDetectionModel(model_type=model_type)
                training_results = model.train(df)
                
                # Add model type to results
                result = {
                    'model_type': model_type,
                    'test_accuracy': training_results.get('test_accuracy', 0),
                    'precision': training_results.get('precision', 0),
                    'recall': training_results.get('recall', 0),
                    'f1_score': training_results.get('f1_score', 0),
                    'auc_score': training_results.get('auc_score', 0)
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error training {model_type}: {e}")
                continue
        
        comparison_df = pd.DataFrame(results)
        comparison_df = comparison_df.sort_values('f1_score', ascending=False)
        
        logger.info("Model comparison results:")
        logger.info(comparison_df)
        
        return comparison_df


if __name__ == "__main__":
    # Example usage
    print("Phishing detection ML model ready!")
    
    # Example of how to use:
    # model = PhishingDetectionModel(model_type='xgboost')
    # results = model.train(processed_df)
    # model.save_model('models/phishing_detector.joblib')
