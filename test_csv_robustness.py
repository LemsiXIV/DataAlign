#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for CSV robustness and encoding handling
Tests the complete chain of fixes implemented for DataAlign v2.0
"""

import os
import sys
import pandas as pd
import tempfile

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.encoding_utils import safe_read_csv, detect_csv_encoding
from app.services.lecteur_fichier import read_uploaded_file
from app.services.lecteur_fichier_optimise import LecteurFichierOptimise

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
    
    # Test 2: CSV with inconsistent columns (the main issue)
    malformed_csv = os.path.join(temp_dir, "malformed.csv")
    with open(malformed_csv, 'w', encoding='utf-8') as f:
        f.write("Name,Age,City\n")
        f.write("John,25,Paris\n")
        f.write("Marie,30,Lyon,Extra,Field,Here\n")  # Too many columns
        f.write("Bob,35\n")  # Too few columns
        f.write("Alice,28,Marseille\n")
    test_files['malformed'] = malformed_csv
    
    # Test 3: CSV with encoding issues (Windows-1252 with accents)
    encoding_csv = os.path.join(temp_dir, "encoding.csv")
    with open(encoding_csv, 'w', encoding='windows-1252') as f:
        f.write("Nom,Âge,Ville\n")
        f.write("François,25,Montréal\n")
        f.write("José,30,León\n")
    test_files['encoding'] = encoding_csv
    
    # Test 4: CSV with different separators
    semicolon_csv = os.path.join(temp_dir, "semicolon.csv")
    with open(semicolon_csv, 'w', encoding='utf-8') as f:
        f.write("Name;Age;City\n")
        f.write("John;25;Paris\n")
        f.write("Marie;30;Lyon\n")
    test_files['semicolon'] = semicolon_csv
    
    return test_files

def test_encoding_detection(test_files):
    """Test encoding detection utilities"""
    print("=== Testing Encoding Detection ===")
    
    for name, file_path in test_files.items():
        try:
            encoding = detect_csv_encoding(file_path)
            print(f"✅ {name}.csv: Detected encoding {encoding}")
        except Exception as e:
            print(f"❌ {name}.csv: Error detecting encoding - {e}")

def test_safe_csv_reading(test_files):
    """Test robust CSV reading"""
    print("\n=== Testing Safe CSV Reading ===")
    
    for name, file_path in test_files.items():
        try:
            df = safe_read_csv(file_path)
            print(f"✅ {name}.csv: Read successfully ({len(df)} rows, {len(df.columns)} columns)")
            if len(df) > 0:
                print(f"   Columns: {list(df.columns)}")
        except Exception as e:
            print(f"❌ {name}.csv: Error reading - {e}")

def test_optimized_reader(test_files):
    """Test optimized file reader"""
    print("\n=== Testing Optimized File Reader ===")
    
    lecteur = LecteurFichierOptimise()
    
    for name, file_path in test_files.items():
        try:
            # Test file info
            file_info = lecteur.read_file_info(file_path)
            print(f"✅ {name}.csv: File info read successfully")
            print(f"   Rows: {file_info.get('rows', 'Unknown')}, Encoding: {file_info.get('encoding', 'Unknown')}")
            
            # Test file sample
            sample = lecteur.get_file_sample(file_path, 2)
            print(f"   Sample: {len(sample)} rows")
            
        except Exception as e:
            print(f"❌ {name}.csv: Error with optimized reader - {e}")

def test_pandas_direct(test_files):
    """Test direct pandas reading (should fail on malformed data)"""
    print("\n=== Testing Direct Pandas Reading (Expected Failures) ===")
    
    for name, file_path in test_files.items():
        try:
            df = pd.read_csv(file_path)
            print(f"✅ {name}.csv: Direct pandas read successful ({len(df)} rows)")
        except Exception as e:
            print(f"❌ {name}.csv: Direct pandas failed - {str(e)[:100]}...")

def cleanup_test_files(test_files):
    """Clean up test files"""
    for file_path in test_files.values():
        if os.path.exists(file_path):
            os.remove(file_path)
    print("\n🧹 Test files cleaned up")

def main():
    """Run all tests"""
    print("DataAlign CSV Robustness Test Suite")
    print("=" * 50)
    
    try:
        # Create test files
        test_files = create_test_csv_files()
        print(f"Created {len(test_files)} test files")
        
        # Run tests
        test_encoding_detection(test_files)
        test_safe_csv_reading(test_files)
        test_optimized_reader(test_files)
        test_pandas_direct(test_files)
        
        print("\n" + "=" * 50)
        print("✅ Test suite completed!")
        print("The robust CSV handling should handle malformed data gracefully")
        print("while direct pandas calls may fail on problematic files.")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
    finally:
        # Cleanup
        if 'test_files' in locals():
            cleanup_test_files(test_files)

if __name__ == "__main__":
    main()
