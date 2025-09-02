#!/usr/bin/env python3
"""
Debug script to investigate Excel export issue in local environment
"""
import os
import pickle
import glob
import pandas as pd
from datetime import datetime

def debug_current_pickle_files():
    """Debug any existing pickle files"""
    print("=== Debugging Current Pickle Files ===")
    print(f"Current time: {datetime.now()}")
    
    # Check temp directory
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        print(f"Temp directory '{temp_dir}' does not exist")
        return
    
    # Find pickle files
    pickle_files = glob.glob(os.path.join(temp_dir, "*.pkl"))
    if not pickle_files:
        print("No pickle files found in temp directory")
        return
    
    print(f"Found {len(pickle_files)} pickle files:")
    for pkl_file in pickle_files:
        print(f"  - {os.path.basename(pkl_file)} (modified: {datetime.fromtimestamp(os.path.getmtime(pkl_file))})")
    
    # Analyze the most recent pickle file
    latest_file = max(pickle_files, key=os.path.getmtime)
    print(f"\nAnalyzing: {os.path.basename(latest_file)}")
    
    try:
        with open(latest_file, 'rb') as f:
            data = pickle.load(f)
        
        print("\n=== Pickle File Contents ===")
        print(f"Keys: {list(data.keys())}")
        
        for key in ['ecarts_fichier1', 'ecarts_fichier2', 'communs']:
            if key in data:
                df = data[key]
                print(f"\n{key}:")
                print(f"  Type: {type(df)}")
                print(f"  Shape: {df.shape}")
                print(f"  Length: {len(df)}")
                
                if len(df) == 1004:
                    print(f"  *** FOUND THE 1004 ISSUE! ***")
                    print(f"  Columns: {list(df.columns)}")
                    if len(df) > 0:
                        print(f"  Sample data:")
                        print(df.head(3).to_string())
                else:
                    print(f"  ✅ Correct count: {len(df)}")
                    
                if len(df) > 0:
                    print(f"  Columns: {list(df.columns)}")
                    if '_merge' in df.columns:
                        print(f"  _merge values: {df['_merge'].value_counts().to_dict()}")
        
        # Check totals
        for key in ['total1', 'total2', 'file1_name', 'file2_name']:
            if key in data:
                print(f"\n{key}: {data[key]}")
                
    except Exception as e:
        print(f"Error reading pickle file: {e}")

def debug_system_temp_files():
    """Check if there are any files in system temp directory"""
    print("\n=== Checking System Temp Directory ===")
    
    import tempfile
    system_temp = tempfile.gettempdir()
    print(f"System temp directory: {system_temp}")
    
    try:
        # Look for pickle files in system temp
        pattern = os.path.join(system_temp, "*.pkl")
        system_pickles = glob.glob(pattern)
        
        if system_pickles:
            print(f"Found {len(system_pickles)} pickle files in system temp:")
            for f in system_pickles[:5]:  # Show only first 5
                print(f"  - {os.path.basename(f)}")
        else:
            print("No pickle files in system temp")
            
        # Look for tmp files that might be our files
        tmp_pattern = os.path.join(system_temp, "tmp*.pkl")
        tmp_files = glob.glob(tmp_pattern)
        
        if tmp_files:
            print(f"Found {len(tmp_files)} tmp*.pkl files:")
            for f in tmp_files[:3]:
                print(f"  - {os.path.basename(f)}")
                
                # Quick check of this file
                try:
                    with open(f, 'rb') as file:
                        data = pickle.load(file)
                    if 'ecarts_fichier1' in data:
                        print(f"    Contains comparison data: {len(data['ecarts_fichier1'])} rows")
                except:
                    print(f"    Could not read file")
        
    except Exception as e:
        print(f"Error checking system temp: {e}")

if __name__ == "__main__":
    print("DataAlign Excel Export Debug - Local Environment")
    print("=" * 50)
    
    debug_current_pickle_files()
    debug_system_temp_files()
    
    print("\n=== Next Steps ===")
    print("1. Run a new comparison")
    print("2. Immediately run this script again") 
    print("3. If 1004 is found, the issue is in the comparison logic")
    print("4. If not found, the issue is in the Excel generation")
