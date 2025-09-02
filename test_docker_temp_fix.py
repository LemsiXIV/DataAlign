#!/usr/bin/env python3
"""
Test script to verify Docker temp file fix for DataAlign Excel export issue.
This script tests the new persistent temp file handling.
"""

import os
import sys
import pickle
import uuid
import pandas as pd

def test_temp_directory_creation():
    """Test that we can create temp directory correctly"""
    print("=== Testing Temp Directory Creation ===")
    
    # Simulate the path calculation from comparaison.py
    # When running in Docker: /app/temp
    # When running locally: ./app/temp (relative to script location)
    
    script_dir = os.path.dirname(__file__)
    temp_dir = os.path.join(script_dir, 'app', 'temp')
    print(f"Expected temp directory: {temp_dir}")
    
    # Create directory
    os.makedirs(temp_dir, exist_ok=True)
    print(f"Directory created/exists: {os.path.exists(temp_dir)}")
    
    return temp_dir

def test_pickle_file_creation(temp_dir):
    """Test creating and reading pickle files in the temp directory"""
    print("\n=== Testing Pickle File Operations ===")
    
    # Create test data similar to comparison results
    test_data = {
        'ecarts_fichier1': pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']}),
        'ecarts_fichier2': pd.DataFrame({'col1': [4, 5], 'col2': ['d', 'e']}),
        'communs': pd.DataFrame({'col1': [6, 7, 8, 9], 'col2': ['f', 'g', 'h', 'i']}),
        'file1_name': 'Test File 1',
        'file2_name': 'Test File 2',
        'total1': 100,
        'total2': 200
    }
    
    # Generate unique filename like in the fixed code
    temp_filename = f"comparison_results_{uuid.uuid4().hex}.pkl"
    temp_path = os.path.join(temp_dir, temp_filename)
    
    print(f"Creating pickle file: {temp_path}")
    
    # Write pickle file
    try:
        with open(temp_path, 'wb') as f:
            pickle.dump(test_data, f)
        print("✅ Pickle file created successfully")
    except Exception as e:
        print(f"❌ Error creating pickle file: {e}")
        return None
    
    # Read pickle file back
    try:
        with open(temp_path, 'rb') as f:
            loaded_data = pickle.load(f)
        print("✅ Pickle file read successfully")
        
        # Verify data integrity
        print(f"Ecarts Fichier 1: {len(loaded_data['ecarts_fichier1'])} rows")
        print(f"Ecarts Fichier 2: {len(loaded_data['ecarts_fichier2'])} rows") 
        print(f"Communs: {len(loaded_data['communs'])} rows")
        
        # Check if any of these are 1004 (the problematic value)
        counts = [
            len(loaded_data['ecarts_fichier1']),
            len(loaded_data['ecarts_fichier2']),
            len(loaded_data['communs'])
        ]
        
        if 1004 in counts:
            print("⚠️ WARNING: Found 1004 in test data!")
        else:
            print("✅ No 1004 values found in test data")
            
    except Exception as e:
        print(f"❌ Error reading pickle file: {e}")
        return None
    
    # Clean up test file
    try:
        os.remove(temp_path)
        print("✅ Test file cleaned up")
    except Exception as e:
        print(f"⚠️ Could not clean up test file: {e}")
    
    return temp_path

def check_docker_environment():
    """Check if we're running in Docker container"""
    print("\n=== Environment Check ===")
    
    # Check for Docker-specific indicators
    if os.path.exists('/.dockerenv'):
        print("✅ Running inside Docker container")
    else:
        print("ℹ️ Not running in Docker (local development)")
    
    print(f"Working directory: {os.getcwd()}")
    print(f"Script location: {os.path.dirname(__file__)}")
    
    # Check if app directory exists
    app_dir = os.path.join(os.path.dirname(__file__), 'app')
    print(f"App directory exists: {os.path.exists(app_dir)}")

def test_file_permissions(temp_dir):
    """Test file permissions in temp directory"""
    print("\n=== Testing File Permissions ===")
    
    test_file = os.path.join(temp_dir, "permission_test.txt")
    
    try:
        # Test write permission
        with open(test_file, 'w') as f:
            f.write("test")
        print("✅ Write permission OK")
        
        # Test read permission
        with open(test_file, 'r') as f:
            content = f.read()
        print("✅ Read permission OK")
        
        # Test delete permission
        os.remove(test_file)
        print("✅ Delete permission OK")
        
    except Exception as e:
        print(f"❌ Permission error: {e}")

if __name__ == "__main__":
    print("DataAlign Docker Temp File Fix - Test Script")
    print("=" * 50)
    
    try:
        check_docker_environment()
        temp_dir = test_temp_directory_creation()
        test_file_permissions(temp_dir)
        test_pickle_file_creation(temp_dir)
        
        print("\n=== Summary ===")
        print("If all tests passed, the Docker temp file fix should work.")
        print("The Excel export should now use persistent temp files in /app/temp")
        print("instead of the non-persistent /tmp directory.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
