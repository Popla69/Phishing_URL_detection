#!/usr/bin/env python3
"""
Test script to verify the phishing detection model works correctly
"""

import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.preprocessing import URLFeatureExtractor
    from app.ml_model import PhishingDetectionModel
    print("✓ Successfully imported modules")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

def test_feature_extraction():
    """Test URL feature extraction"""
    print("\n=== Testing Feature Extraction ===")
    
    extractor = URLFeatureExtractor()
    
    # Test URLs
    test_urls = [
        "https://www.google.com",
        "http://suspicious-banking-site.fake.com/login",
        "https://github.com/microsoft/vscode",
        "http://phishing-paypal.scam.com/verify-account"
    ]
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        try:
            features = extractor.extract_all_features(url)
            print(f"  ✓ Extracted {len(features)} features")
            print(f"  ✓ URL length: {features.get('url_length', 'N/A')}")
            print(f"  ✓ Has HTTPS: {features.get('has_https', 'N/A')}")
            print(f"  ✓ Phishing keywords: {features.get('num_phishing_keywords', 'N/A')}")
            print(f"  ✓ Domain entropy: {features.get('domain_entropy', 'N/A'):.2f}")
        except Exception as e:
            print(f"  ✗ Error extracting features: {e}")

def test_model_loading():
    """Test loading the trained model"""
    print("\n=== Testing Model Loading ===")
    
    model_path = Path("models/phishing_detector.joblib")
    
    if not model_path.exists():
        print(f"✗ Model file not found: {model_path}")
        return None
    
    try:
        model = PhishingDetectionModel()
        model.load_model(str(model_path))
        print(f"✓ Successfully loaded model: {model.model_type}")
        print(f"✓ Model is trained: {model.is_trained}")
        print(f"✓ Feature count: {len(model.feature_columns)}")
        return model
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        return None

def test_predictions(model):
    """Test making predictions with the model"""
    if not model:
        print("✗ Cannot test predictions - model not loaded")
        return
    
    print("\n=== Testing Predictions ===")
    
    extractor = URLFeatureExtractor()
    
    # Test URLs with expected results
    test_cases = [
        ("https://www.google.com", "Legitimate", False),
        ("https://github.com", "Legitimate", False),
        ("http://suspicious-banking-site.fake.com/login", "Suspicious", True),
        ("http://phishing-paypal.scam.com/verify", "Suspicious", True),
        ("https://www.microsoft.com", "Legitimate", False),
        ("http://fake-amazon-login.malicious.org/signin", "Suspicious", True)
    ]
    
    print(f"{'URL':<50} {'Expected':<12} {'Predicted':<12} {'Confidence':<12} {'Risk Level':<12}")
    print("=" * 100)
    
    for url, expected, _ in test_cases:
        try:
            # Extract features
            features = extractor.extract_all_features(url)
            
            # Make prediction
            result = model.predict(features)
            
            predicted = "Phishing" if result['is_phishing'] else "Legitimate"
            confidence = f"{result['confidence']:.2f}"
            risk_level = "HIGH" if result['phishing_probability'] >= 0.7 else "MEDIUM" if result['phishing_probability'] >= 0.4 else "LOW"
            
            print(f"{url:<50} {expected:<12} {predicted:<12} {confidence:<12} {risk_level:<12}")
            
        except Exception as e:
            print(f"{url:<50} {expected:<12} {'ERROR':<12} {'N/A':<12} {'N/A':<12}")
            print(f"  Error: {e}")

def test_batch_processing():
    """Test batch URL processing"""
    print("\n=== Testing Batch Processing ===")
    
    model_path = Path("models/phishing_detector.joblib")
    if not model_path.exists():
        print("✗ Model file not found - skipping batch test")
        return
    
    try:
        model = PhishingDetectionModel()
        model.load_model(str(model_path))
        extractor = URLFeatureExtractor()
        
        # Batch of URLs
        urls = [
            "https://www.google.com",
            "https://www.github.com",
            "http://suspicious-site.com/login",
            "https://www.microsoft.com",
            "http://fake-paypal.scam.com/verify"
        ]
        
        print(f"Testing batch processing with {len(urls)} URLs...")
        
        results = []
        for url in urls:
            features = extractor.extract_all_features(url)
            result = model.predict(features)
            results.append({
                'url': url,
                'is_phishing': result['is_phishing'],
                'confidence': result['confidence']
            })
        
        print("✓ Batch processing completed")
        
        phishing_count = sum(1 for r in results if r['is_phishing'])
        legitimate_count = len(results) - phishing_count
        
        print(f"  Results: {phishing_count} phishing, {legitimate_count} legitimate")
        
    except Exception as e:
        print(f"✗ Batch processing error: {e}")

def main():
    """Run all tests"""
    print("🔍 PHISHING DETECTION SYSTEM TEST")
    print("=" * 50)
    
    # Test 1: Feature extraction
    test_feature_extraction()
    
    # Test 2: Model loading
    model = test_model_loading()
    
    # Test 3: Individual predictions
    test_predictions(model)
    
    # Test 4: Batch processing
    test_batch_processing()
    
    print("\n" + "=" * 50)
    print("🎉 TESTING COMPLETED!")
    print("\nIf all tests passed, your phishing detection system is working correctly!")
    print("You can now integrate this into a web application or use it directly in Python scripts.")

if __name__ == "__main__":
    main()
