#!/usr/bin/env python3
"""
Package installer script that works around pip issues
"""

import subprocess
import sys
import os
from pathlib import Path

def install_package(package_name):
    """Install a package using various methods"""
    methods = [
        # Method 1: Direct pip
        [sys.executable, "-m", "pip", "install", package_name],
        # Method 2: pip with --user flag
        [sys.executable, "-m", "pip", "install", "--user", package_name],
        # Method 3: ensurepip then pip
        [sys.executable, "-m", "ensurepip", "--upgrade"],
    ]
    
    for method in methods:
        try:
            print(f"Trying to install {package_name} with method: {' '.join(method)}")
            result = subprocess.run(method, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=300)
            
            if result.returncode == 0:
                print(f"✓ Successfully installed {package_name}")
                return True
            else:
                print(f"✗ Method failed: {result.stderr[:200]}")
                
        except Exception as e:
            print(f"✗ Method failed with exception: {e}")
            continue
    
    return False

def main():
    """Install essential packages"""
    packages = [
        "numpy",
        "pandas", 
        "scikit-learn",
        "xgboost",
        "joblib"
    ]
    
    print("Installing essential ML packages...")
    
    for package in packages:
        print(f"\n--- Installing {package} ---")
        success = install_package(package)
        
        if not success:
            print(f"Failed to install {package}. You may need to install it manually.")
            print(f"Try: python -m pip install {package}")
        
    print("\n=== Installation Summary ===")
    
    # Test imports
    for package in ["numpy", "pandas", "sklearn", "xgboost", "joblib"]:
        try:
            if package == "sklearn":
                import sklearn
            else:
                __import__(package)
            print(f"✓ {package} is available")
        except ImportError:
            print(f"✗ {package} is NOT available")

if __name__ == "__main__":
    main()
