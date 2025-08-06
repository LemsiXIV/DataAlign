"""
Test script to demonstrate the performance improvements for large file handling
"""
import pandas as pd
import numpy as np
import time
import os
import sys
from datetime import datetime

# Add the app directory to the path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.comparateur import ComparateurFichiers
from app.services.comparateur_optimise import ComparateurFichiersOptimise, compare_large_files
from app.services.lecteur_fichier_optimise import LecteurFichierOptimise

def create_test_files():
    """Create test files with different sizes for performance testing"""
    print("Creating test files...")
    
    # Create large test file 1 (15,000 rows, 150 columns)
    np.random.seed(42)
    data1 = {}
    
    # Create key columns
    data1['id'] = range(1, 15001)
    data1['code'] = [f"CODE_{i:05d}" for i in range(1, 15001)]
    data1['name'] = [f"Name_{i}" for i in range(1, 15001)]
    
    # Create 147 additional columns with random data
    for i in range(4, 151):
        if i % 3 == 0:
            data1[f'col_{i}'] = np.random.choice(['A', 'B', 'C', 'D'], 15000)
        elif i % 3 == 1:
            data1[f'col_{i}'] = np.random.randint(1, 1000, 15000)
        else:
            data1[f'col_{i}'] = np.random.normal(100, 15, 15000)
    
    df1 = pd.DataFrame(data1)
    
    # Create large test file 2 (similar structure but with some differences)
    data2 = {}
    
    # Mix of overlapping and different IDs
    overlapping_ids = list(range(1, 12001))  # 80% overlap
    unique_ids = list(range(15001, 18001))   # 20% unique
    all_ids = overlapping_ids + unique_ids
    np.random.shuffle(all_ids)
    
    data2['id'] = all_ids[:15000]
    data2['code'] = [f"CODE_{i:05d}" for i in data2['id']]
    data2['name'] = [f"Name_{i}" for i in data2['id']]
    
    # Create 147 additional columns with random data
    for i in range(4, 151):
        if i % 3 == 0:
            data2[f'col_{i}'] = np.random.choice(['A', 'B', 'C', 'D'], 15000)
        elif i % 3 == 1:
            data2[f'col_{i}'] = np.random.randint(1, 1000, 15000)
        else:
            data2[f'col_{i}'] = np.random.normal(100, 15, 15000)
    
    df2 = pd.DataFrame(data2)
    
    # Save files
    df1.to_csv('test_large_file1.csv', index=False)
    df2.to_csv('test_large_file2.csv', index=False)
    
    print(f"Created test_large_file1.csv: {len(df1)} rows, {len(df1.columns)} columns")
    print(f"Created test_large_file2.csv: {len(df2)} rows, {len(df2.columns)} columns")
    print(f"File 1 size: {os.path.getsize('test_large_file1.csv') / 1024 / 1024:.2f} MB")
    print(f"File 2 size: {os.path.getsize('test_large_file2.csv') / 1024 / 1024:.2f} MB")
    
    return 'test_large_file1.csv', 'test_large_file2.csv'

def test_traditional_approach(file1, file2, keys1, keys2):
    """Test the traditional approach"""
    print("\n=== Testing Traditional Approach ===")
    start_time = time.time()
    
    try:
        # Read files
        print("Reading files...")
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
        
        read_time = time.time()
        print(f"File reading time: {read_time - start_time:.2f} seconds")
        
        # Compare
        print("Comparing files...")
        comparateur = ComparateurFichiers(df1, df2, keys1, keys2)
        results = comparateur.comparer()
        
        compare_time = time.time()
        print(f"Comparison time: {compare_time - read_time:.2f} seconds")
        print(f"Total time: {compare_time - start_time:.2f} seconds")
        
        print(f"Results: {results['n_common']} common, {results['n1']} unique in file1, {results['n2']} unique in file2")
        
        return compare_time - start_time
        
    except Exception as e:
        print(f"Traditional approach failed: {e}")
        return None

def test_optimized_approach(file1, file2, keys1, keys2):
    """Test the optimized approach"""
    print("\n=== Testing Optimized Approach ===")
    start_time = time.time()
    
    try:
        # Use optimized comparator
        print("Starting optimized comparison...")
        comparateur = ComparateurFichiersOptimise(file1, file2, keys1, keys2, chunk_size=2000)
        results = comparateur.comparer_optimise(sample_size=1000)
        
        compare_time = time.time()
        print(f"Total optimized time: {compare_time - start_time:.2f} seconds")
        
        print(f"Results: {results['n_common']} common, {results['n1']} unique in file1, {results['n2']} unique in file2")
        
        # Clean up
        comparateur.cleanup()
        
        return compare_time - start_time
        
    except Exception as e:
        print(f"Optimized approach failed: {e}")
        return None

def test_file_info_reading(file1, file2):
    """Test quick file info reading"""
    print("\n=== Testing File Info Reading ===")
    start_time = time.time()
    
    lecteur = LecteurFichierOptimise()
    
    # Get file info without loading entire files
    info1 = lecteur.read_file_info(file1)
    info2 = lecteur.read_file_info(file2)
    
    info_time = time.time()
    print(f"File info reading time: {info_time - start_time:.2f} seconds")
    
    print(f"File 1: {info1['total_rows']} rows, {info1['total_columns']} columns")
    print(f"File 2: {info2['total_rows']} rows, {info2['total_columns']} columns")
    
    # Get samples
    sample1 = lecteur.get_file_sample(file1, 100)
    sample2 = lecteur.get_file_sample(file2, 100)
    
    sample_time = time.time()
    print(f"Sample reading time: {sample_time - info_time:.2f} seconds")
    print(f"Sample 1: {len(sample1)} rows")
    print(f"Sample 2: {len(sample2)} rows")

def main():
    """Main test function"""
    print("=== Large File Performance Test ===")
    print(f"Test started at: {datetime.now()}")
    
    # Create test files
    file1, file2 = create_test_files()
    
    # Define comparison keys
    keys1 = ['id', 'code']
    keys2 = ['id', 'code']
    
    # Test file info reading
    test_file_info_reading(file1, file2)
    
    # Test optimized approach first (more likely to succeed)
    optimized_time = test_optimized_approach(file1, file2, keys1, keys2)
    
    # Test traditional approach
    traditional_time = test_traditional_approach(file1, file2, keys1, keys2)
    
    # Compare results
    if optimized_time and traditional_time:
        improvement = traditional_time / optimized_time
        print(f"\n=== Performance Comparison ===")
        print(f"Traditional approach: {traditional_time:.2f} seconds")
        print(f"Optimized approach: {optimized_time:.2f} seconds")
        print(f"Performance improvement: {improvement:.2f}x faster")
    elif optimized_time:
        print(f"\n=== Results ===")
        print(f"Optimized approach succeeded: {optimized_time:.2f} seconds")
        print("Traditional approach failed (likely due to memory constraints)")
    
    # Clean up test files
    try:
        os.remove(file1)
        os.remove(file2)
        print("\nTest files cleaned up.")
    except:
        pass

if __name__ == "__main__":
    main()
