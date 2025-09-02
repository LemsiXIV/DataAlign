#!/usr/bin/env python3
"""
Debug script to investigate the Excel export data discrepancy issue.
This script will help identify where the "1004" values are coming from.
"""

import os
import sys
import glob
import pickle
import pandas as pd

def debug_pickle_files():
    """Debug any existing pickle files in temp directory"""
    print("=== DataAlign Excel Export Debug ===\n")
    
    # Look for pickle files in temp directory
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
    pickle_files = glob.glob(os.path.join(temp_dir, '*.pkl'))
    
    if not pickle_files:
        print("No pickle files found in temp directory.")
        return
    
    print(f"Found {len(pickle_files)} pickle files:")
    for pkl_file in pickle_files:
        print(f"  - {os.path.basename(pkl_file)}")
    
    # Examine the most recent pickle file
    latest_file = max(pickle_files, key=os.path.getmtime)
    print(f"\nAnalyzing latest file: {os.path.basename(latest_file)}")
    
    try:
        with open(latest_file, 'rb') as f:
            data = pickle.load(f)
        
        print("\n=== Pickle File Contents ===")
        print(f"Keys in pickle file: {list(data.keys())}")
        
        for key in ['ecarts_fichier1', 'ecarts_fichier2', 'communs']:
            if key in data:
                df = data[key]
                print(f"\n{key}:")
                print(f"  Type: {type(df)}")
                print(f"  Shape: {df.shape}")
                print(f"  Length: {len(df)}")
                if len(df) > 0:
                    print(f"  Columns: {list(df.columns)}")
                    print(f"  First few rows:")
                    print(df.head(3).to_string(index=False))
                else:
                    print("  DataFrame is empty")
        
        # Check other metadata
        for key in ['file1_name', 'file2_name', 'total1', 'total2']:
            if key in data:
                print(f"\n{key}: {data[key]}")
                
    except Exception as e:
        print(f"Error reading pickle file: {e}")

def simulate_excel_generation():
    """Simulate the Excel generation process to see where issue occurs"""
    print("\n=== Simulating Excel Generation ===")
    
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
    pickle_files = glob.glob(os.path.join(temp_dir, '*.pkl'))
    
    if not pickle_files:
        print("No pickle files to test with.")
        return
    
    latest_file = max(pickle_files, key=os.path.getmtime)
    
    try:
        with open(latest_file, 'rb') as f:
            resultats = pickle.load(f)
        
        # Simulate what GenerateurExcel does
        ecarts1 = resultats['ecarts_fichier1']
        ecarts2 = resultats['ecarts_fichier2']
        communs = resultats['communs']
        
        # Drop comparison columns like the Excel generator does
        only1 = ecarts1.drop(columns=['_compare_key', '_merge'], errors='ignore')
        only2 = ecarts2.drop(columns=['_compare_key', '_merge'], errors='ignore')
        both = communs.drop(columns=['_compare_key', '_merge'], errors='ignore')
        
        print(f"\nAfter column drops (like Excel generator):")
        print(f"  Ecarts Fichier 1: {len(only1)} rows")
        print(f"  Ecarts Fichier 2: {len(only2)} rows") 
        print(f"  Communs: {len(both)} rows")
        
        # Check if any of these numbers are 1004
        if len(only1) == 1004 or len(only2) == 1004 or len(both) == 1004:
            print("\n*** FOUND THE 1004 VALUE! ***")
            print("This confirms the data is already corrupted before Excel generation.")
        
    except Exception as e:
        print(f"Error in simulation: {e}")

def check_temp_directory():
    """Check what's in the temp directory"""
    print("\n=== Temp Directory Contents ===")
    
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
    if not os.path.exists(temp_dir):
        print("Temp directory does not exist.")
        return
    
    files = os.listdir(temp_dir)
    print(f"Files in temp directory: {len(files)}")
    
    for file in files:
        file_path = os.path.join(temp_dir, file)
        size = os.path.getsize(file_path)
        print(f"  {file} ({size} bytes)")

if __name__ == "__main__":
    check_temp_directory()
    debug_pickle_files()
    simulate_excel_generation()
    
    print("\n=== Next Steps ===")
    print("1. If 1004 values found in pickle files, the issue is in comparaison.py")
    print("2. If pickle files look correct, the issue is in generateur_excel.py")
    print("3. Run a new comparison and immediately run this script to debug fresh data")
