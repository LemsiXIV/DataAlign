#!/usr/bin/env python3
"""
Simple debug script - no pandas dependency
"""
import os
import glob
import pickle

def check_temp_directory():
    print("=== Checking temp directory ===")
    temp_dir = "temp"
    
    if not os.path.exists(temp_dir):
        print(f"temp directory does not exist: {os.path.abspath(temp_dir)}")
        return None
    
    files = os.listdir(temp_dir)
    print(f"Files in temp: {files}")
    
    pickle_files = [f for f in files if f.endswith('.pkl')]
    print(f"Pickle files: {pickle_files}")
    
    return temp_dir, pickle_files

def check_pickle_content(temp_dir, pickle_files):
    if not pickle_files:
        print("No pickle files to analyze")
        return
    
    latest_file = max([os.path.join(temp_dir, f) for f in pickle_files], 
                     key=os.path.getmtime)
    
    print(f"\nAnalyzing: {latest_file}")
    
    try:
        with open(latest_file, 'rb') as f:
            data = pickle.load(f)
        
        print(f"Keys in pickle: {list(data.keys())}")
        
        for key in ['ecarts_fichier1', 'ecarts_fichier2', 'communs']:
            if key in data:
                df = data[key]
                count = len(df)
                print(f"{key}: {count} rows")
                if count == 1004:
                    print(f"  *** FOUND 1004 IN {key}! ***")
    except Exception as e:
        print(f"Error reading pickle: {e}")

if __name__ == "__main__":
    result = check_temp_directory()
    if result:
        temp_dir, pickle_files = result
        check_pickle_content(temp_dir, pickle_files)
    
    print("\nPlease run a comparison first, then run this script again.")
