#!/usr/bin/env python3
"""
Quick Start Script for Phishing URL Detection Backend

This script helps users get started quickly by:
1. Creating sample data if no dataset is provided
2. Training a model with the sample data
3. Starting the API server

Usage:
    python quick_start.py
    python quick_start.py --dataset path/to/your/dataset.csv
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def create_sample_data():
    """Create sample data for testing if no real dataset is provided"""
    sample_data = """url,label
https://www.google.com,0
https://www.github.com,0
https://www.stackoverflow.com,0
https://www.microsoft.com,0
https://www.amazon.com,0
https://www.facebook.com,0
https://www.twitter.com,0
https://www.linkedin.com,0
https://www.youtube.com,0
https://www.wikipedia.org,0
http://suspicious-banking-site.fake.com/login,1
http://phishing-paypal.scam.com/verify,1
http://fake-amazon-login.malicious.org/signin,1
http://microsoft-security-alert.phish.net/update,1
http://google-account-suspended.evil.com/verify,1
http://facebook-security-check.phish.net/login,1
http://twitter-verify-account.fake.com/signin,1
http://linkedin-profile-update.scam.org/update,1
http://youtube-copyright-notice.evil.net/verify,1
http://wikipedia-donation-urgent.phish.com/donate,1
"""
    
    sample_file = Path("data/sample_dataset.csv")
    sample_file.parent.mkdir(exist_ok=True)
    
    with open(sample_file, 'w') as f:
        f.write(sample_data)
    
    print(f"Created sample dataset at {sample_file}")
    return str(sample_file)

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import pandas
        import sklearn
        import fastapi
        import uvicorn
        print("✓ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def train_model(dataset_path):
    """Train the model using the provided dataset"""
    print(f"Training model with dataset: {dataset_path}")
    
    cmd = [
        sys.executable, "train_model.py",
        "--dataset", dataset_path,
        "--model-type", "xgboost",
        "--sample-size", "1000"  # Use sample for quick start
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Model training completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Model training failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False

def start_api_server():
    """Start the API server"""
    print("Starting API server...")
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n✓ API server stopped")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to start API server: {e}")

def main():
    parser = argparse.ArgumentParser(description='Quick Start for Phishing URL Detection')
    parser.add_argument('--dataset', help='Path to your dataset CSV file')
    parser.add_argument('--skip-training', action='store_true', help='Skip model training')
    parser.add_argument('--port', default=8000, type=int, help='API server port')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 PHISHING URL DETECTION - QUICK START")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create directories
    for dir_name in ['models', 'data', 'logs']:
        Path(dir_name).mkdir(exist_ok=True)
    
    # Determine dataset path
    if args.dataset and Path(args.dataset).exists():
        dataset_path = args.dataset
        print(f"Using provided dataset: {dataset_path}")
    else:
        if args.dataset:
            print(f"Dataset not found: {args.dataset}")
        print("Creating sample dataset for demonstration...")
        dataset_path = create_sample_data()
    
    # Train model unless skipped
    if not args.skip_training:
        if not train_model(dataset_path):
            print("Model training failed. You can still start the API, but predictions won't work.")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
    else:
        print("Skipping model training")
    
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    print(f"API Documentation: http://localhost:{args.port}/docs")
    print(f"Health Check: http://localhost:{args.port}/health")
    print(f"API Status: http://localhost:{args.port}/status")
    print("\nExample API call:")
    print(f'curl -X POST "http://localhost:{args.port}/check-url" \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"url": "http://suspicious-site.com/login"}\'')
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    # Start API server
    start_api_server()

if __name__ == "__main__":
    main()
