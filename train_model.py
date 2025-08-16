#!/usr/bin/env python3
"""
Training script for the Phishing URL Detection model
This script processes the 54k+ URL dataset and trains the ML model
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import logging
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.preprocessing import DataPreprocessor
from app.ml_model import PhishingDetectionModel, ModelEvaluator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_and_validate_dataset(file_path: str, url_column: str = 'url', label_column: str = 'label'):
    """
    Load and validate the dataset
    
    Args:
        file_path: Path to the CSV file containing the dataset
        url_column: Name of the column containing URLs
        label_column: Name of the column containing labels (0=legitimate, 1=phishing)
    
    Returns:
        pandas.DataFrame: Loaded and validated dataset
    """
    logger.info(f"Loading dataset from {file_path}")
    
    # Check if file exists
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    # Load dataset
    df = pd.read_csv(file_path)
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
    logger.info(f"Columns: {list(df.columns)}")
    
    # Validate required columns
    if url_column not in df.columns:
        logger.error(f"URL column '{url_column}' not found in dataset")
        logger.info("Available columns: " + ", ".join(df.columns))
        
        # Try to auto-detect URL column
        possible_url_columns = ['url', 'URL', 'link', 'website', 'site']
        for col in possible_url_columns:
            if col in df.columns:
                logger.info(f"Auto-detected URL column: {col}")
                url_column = col
                break
        else:
            raise ValueError(f"Could not find URL column. Available columns: {list(df.columns)}")
    
    if label_column not in df.columns:
        logger.error(f"Label column '{label_column}' not found in dataset")
        logger.info("Available columns: " + ", ".join(df.columns))
        
        # Try to auto-detect label column
        possible_label_columns = ['label', 'class', 'type', 'classification', 'is_phishing', 'phishing']
        for col in possible_label_columns:
            if col in df.columns:
                logger.info(f"Auto-detected label column: {col}")
                label_column = col
                break
        else:
            raise ValueError(f"Could not find label column. Available columns: {list(df.columns)}")
    
    # Rename columns for consistency
    df = df.rename(columns={url_column: 'url', label_column: 'label'})
    
    # Validate data types and clean
    logger.info("Validating dataset...")
    
    # Remove empty URLs
    initial_size = len(df)
    df = df.dropna(subset=['url'])
    df = df[df['url'].str.strip() != '']
    logger.info(f"Removed {initial_size - len(df)} empty URLs")
    
    # Validate labels
    unique_labels = df['label'].unique()
    logger.info(f"Unique labels found: {unique_labels}")
    
    # Convert labels to binary if needed
    if set(unique_labels) == {'legitimate', 'phishing'}:
        df['label'] = df['label'].map({'legitimate': 0, 'phishing': 1})
        logger.info("Converted string labels to binary (0=legitimate, 1=phishing)")
    elif set(unique_labels) == {'ham', 'spam'}:
        df['label'] = df['label'].map({'ham': 0, 'spam': 1})
        logger.info("Converted ham/spam labels to binary (0=legitimate, 1=phishing)")
    elif set(unique_labels) == {'good', 'bad'}:
        df['label'] = df['label'].map({'good': 0, 'bad': 1})
        logger.info("Converted good/bad labels to binary (0=legitimate, 1=phishing)")
    elif not set(unique_labels).issubset({0, 1}):
        logger.warning(f"Unexpected label values: {unique_labels}")
        logger.info("Attempting to convert to binary...")
        # Try to convert to numeric
        df['label'] = pd.to_numeric(df['label'], errors='coerce')
        df = df.dropna(subset=['label'])
        df['label'] = df['label'].astype(int)
    
    # Final validation
    final_labels = df['label'].unique()
    if not set(final_labels).issubset({0, 1}):
        raise ValueError(f"Invalid label values after conversion: {final_labels}. Expected only 0 and 1.")
    
    # Show class distribution
    class_counts = df['label'].value_counts().sort_index()
    logger.info(f"Class distribution:")
    logger.info(f"  Legitimate (0): {class_counts.get(0, 0)} ({class_counts.get(0, 0)/len(df)*100:.1f}%)")
    logger.info(f"  Phishing (1): {class_counts.get(1, 0)} ({class_counts.get(1, 0)/len(df)*100:.1f}%)")
    
    logger.info(f"Final dataset size: {len(df)} samples")
    
    return df

def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description='Train Phishing URL Detection Model')
    parser.add_argument('--dataset', '-d', required=True, help='Path to the dataset CSV file')
    parser.add_argument('--url-column', default='url', help='Name of the URL column (default: url)')
    parser.add_argument('--label-column', default='label', help='Name of the label column (default: label)')
    parser.add_argument('--model-type', default='xgboost', 
                       choices=['xgboost', 'random_forest', 'gradient_boost', 'logistic', 'svm'],
                       help='Type of model to train (default: xgboost)')
    parser.add_argument('--output-dir', default='models', help='Directory to save the trained model')
    parser.add_argument('--compare-models', action='store_true', 
                       help='Compare multiple model types')
    parser.add_argument('--hyperparameter-tuning', action='store_true',
                       help='Perform hyperparameter tuning')
    parser.add_argument('--cross-validation', action='store_true',
                       help='Perform cross-validation')
    parser.add_argument('--sample-size', type=int, 
                       help='Use only a sample of the dataset (for testing)')
    
    args = parser.parse_args()
    
    try:
        logger.info("=" * 50)
        logger.info("PHISHING URL DETECTION MODEL TRAINING")
        logger.info("=" * 50)
        logger.info(f"Started at: {datetime.now()}")
        
        # Load dataset
        df = load_and_validate_dataset(args.dataset, args.url_column, args.label_column)
        
        # Sample dataset if requested (for testing)
        if args.sample_size and args.sample_size < len(df):
            logger.info(f"Sampling {args.sample_size} rows from dataset for testing...")
            df = df.sample(n=args.sample_size, random_state=42)
        
        # Initialize preprocessor
        logger.info("Initializing data preprocessor...")
        preprocessor = DataPreprocessor()
        
        # Preprocess dataset (extract features)
        logger.info("Starting feature extraction...")
        processed_df = preprocessor.preprocess_dataset(df)
        
        # Clean data
        logger.info("Cleaning processed data...")
        cleaned_df = preprocessor.clean_data(processed_df)
        
        # Save processed data
        processed_data_path = Path('data') / 'processed_features.csv'
        processed_data_path.parent.mkdir(exist_ok=True)
        preprocessor.save_processed_data(cleaned_df, str(processed_data_path))
        
        # Model comparison if requested
        if args.compare_models:
            logger.info("Comparing multiple model types...")
            comparison_results = ModelEvaluator.compare_models(cleaned_df)
            logger.info("Model comparison completed")
            
            # Save comparison results
            comparison_path = Path(args.output_dir) / 'model_comparison.csv'
            comparison_path.parent.mkdir(exist_ok=True)
            comparison_results.to_csv(comparison_path, index=False)
            logger.info(f"Comparison results saved to {comparison_path}")
        
        # Train the specified model
        logger.info(f"Training {args.model_type} model...")
        model = PhishingDetectionModel(model_type=args.model_type)
        
        # Perform hyperparameter tuning if requested
        if args.hyperparameter_tuning:
            logger.info("Performing hyperparameter tuning...")
            tuning_results = model.hyperparameter_tuning(cleaned_df)
            logger.info("Hyperparameter tuning completed")
        
        # Perform cross-validation if requested
        if args.cross_validation:
            logger.info("Performing cross-validation...")
            cv_results = model.cross_validate(cleaned_df)
            logger.info("Cross-validation completed")
        
        # Train final model
        training_results = model.train(cleaned_df)
        
        # Display results
        logger.info("=" * 50)
        logger.info("TRAINING RESULTS")
        logger.info("=" * 50)
        logger.info(f"Model Type: {args.model_type}")
        logger.info(f"Dataset Size: {len(cleaned_df)} samples")
        logger.info(f"Features: {len(cleaned_df.columns) - 1}")
        
        if 'test_accuracy' in training_results:
            logger.info(f"Test Accuracy: {training_results['test_accuracy']:.4f}")
            logger.info(f"Precision: {training_results['precision']:.4f}")
            logger.info(f"Recall: {training_results['recall']:.4f}")
            logger.info(f"F1 Score: {training_results['f1_score']:.4f}")
            logger.info(f"AUC Score: {training_results['auc_score']:.4f}")
        
        # Save the trained model
        model_dir = Path(args.output_dir)
        model_dir.mkdir(exist_ok=True)
        model_path = model_dir / f'phishing_detector_{args.model_type}.joblib'
        model.save_model(str(model_path))
        
        # Also save as the default model
        default_model_path = model_dir / 'phishing_detector.joblib'
        model.save_model(str(default_model_path))
        logger.info(f"Model saved to {model_path}")
        logger.info(f"Default model saved to {default_model_path}")
        
        # Save training report
        report = {
            'timestamp': datetime.now().isoformat(),
            'model_type': args.model_type,
            'dataset_path': args.dataset,
            'dataset_size': len(cleaned_df),
            'feature_count': len(cleaned_df.columns) - 1,
            'training_results': training_results
        }
        
        import json
        report_path = model_dir / f'training_report_{args.model_type}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Training report saved to {report_path}")
        logger.info("=" * 50)
        logger.info("TRAINING COMPLETED SUCCESSFULLY!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
