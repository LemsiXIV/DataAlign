#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple CSV robustness test without Flask dependencies
"""

import os
import pandas as pd

def create_test_csv_files():
    """Create test CSV files with various problematic scenarios"""
    test_files = {}
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Test 1: Normal CSV
    normal_csv = os.path.join(temp_dir, "normal.csv")
    with open(normal_csv, 'w', encoding='utf-8') as f:
        f.write("Name,Age,City\n")
        f.write("John,25,Paris\n")
        f.write("Marie,30,Lyon\n")
    test_files['normal'] = normal_csv
    
    # Test 2: CSV with inconsistent columns (the main issue we're fixing)
    malformed_csv = os.path.join(temp_dir, "malformed.csv")
    with open(malformed_csv, 'w', encoding='utf-8') as f:
        f.write("Name,Age,City\n")
        f.write("John,25,Paris\n")
        f.write("Marie,30,Lyon,Extra,Field,Here\n")  # Too many columns
        f.write("Bob,35\n")  # Too few columns
        f.write("Alice,28,Marseille\n")
    test_files['malformed'] = malformed_csv
    
    return test_files

def test_pandas_default_vs_robust():
    """Test pandas default behavior vs robust parameters"""
    print("=== CSV Robustness Test ===")
    
    test_files = create_test_csv_files()
    
    for name, file_path in test_files.items():
        print(f"\nTesting {name}.csv:")
        
        # Test 1: Default pandas (should fail on malformed)
        try:
            df_default = pd.read_csv(file_path)
            print(f"  ✅ Default pandas: {len(df_default)} rows, {len(df_default.columns)} columns")
        except Exception as e:
            print(f"  ❌ Default pandas failed: {str(e)[:60]}...")
        
        # Test 2: Robust pandas (should handle malformed)
        try:
            df_robust = pd.read_csv(file_path, on_bad_lines='skip', engine='python')
            print(f"  ✅ Robust pandas: {len(df_robust)} rows, {len(df_robust.columns)} columns")
        except Exception as e:
            print(f"  ❌ Robust pandas failed: {str(e)[:60]}...")
    
    # Cleanup
    for file_path in test_files.values():
        if os.path.exists(file_path):
            os.remove(file_path)
    
    print("\n✅ Test completed - robust parameters should handle malformed CSV files!")

if __name__ == "__main__":
    test_pandas_default_vs_robust()
