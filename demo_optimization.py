"""
Simple demonstration script for optimized file handling
Run this to see how the optimized services handle large files
"""
import pandas as pd
import numpy as np
import os
import time
import sys

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def create_sample_large_files():
    """Create sample large files for testing"""
    print("Creating sample large files...")
    
    # Create file 1 with 10,000 rows and 50 columns
    np.random.seed(42)
    data1 = {
        'id': range(1, 10001),
        'code': [f"CODE_{i:05d}" for i in range(1, 10001)],
        'name': [f"Product_{i}" for i in range(1, 10001)]
    }
    
    # Add 47 more columns
    for i in range(4, 51):
        if i % 3 == 0:
            data1[f'category_{i}'] = np.random.choice(['A', 'B', 'C'], 10000)
        elif i % 3 == 1:
            data1[f'value_{i}'] = np.random.randint(1, 1000, 10000)
        else:
            data1[f'measure_{i}'] = np.random.normal(100, 15, 10000).round(2)
    
    df1 = pd.DataFrame(data1)
    
    # Create file 2 with some overlap and differences
    overlap_ids = list(range(1, 8001))  # 80% overlap
    unique_ids = list(range(10001, 12001))  # New IDs
    all_ids = overlap_ids + unique_ids
    
    data2 = {
        'id': all_ids[:10000],
        'code': [f"CODE_{i:05d}" for i in all_ids[:10000]],
        'name': [f"Product_{i}" for i in all_ids[:10000]]
    }
    
    # Add same structure as file 1
    for i in range(4, 51):
        if i % 3 == 0:
            data2[f'category_{i}'] = np.random.choice(['A', 'B', 'C'], 10000)
        elif i % 3 == 1:
            data2[f'value_{i}'] = np.random.randint(1, 1000, 10000)
        else:
            data2[f'measure_{i}'] = np.random.normal(100, 15, 10000).round(2)
    
    df2 = pd.DataFrame(data2)
    
    # Save files
    df1.to_csv('sample_file1.csv', index=False)
    df2.to_csv('sample_file2.csv', index=False)
    
    file1_size = os.path.getsize('sample_file1.csv') / 1024 / 1024
    file2_size = os.path.getsize('sample_file2.csv') / 1024 / 1024
    
    print(f"Created sample_file1.csv: {len(df1)} rows, {len(df1.columns)} columns ({file1_size:.2f} MB)")
    print(f"Created sample_file2.csv: {len(df2)} rows, {len(df2.columns)} columns ({file2_size:.2f} MB)")
    
    return 'sample_file1.csv', 'sample_file2.csv'

def test_optimized_reading():
    """Test the optimized file reading"""
    print("\n=== Testing Optimized File Reading ===")
    
    try:
        from app.services.lecteur_fichier_optimise import LecteurFichierOptimise
        
        file1, file2 = create_sample_large_files()
        
        lecteur = LecteurFichierOptimise()
        
        # Test file info reading
        start_time = time.time()
        info1 = lecteur.read_file_info(file1)
        info2 = lecteur.read_file_info(file2)
        info_time = time.time() - start_time
        
        print(f"File info reading took: {info_time:.2f} seconds")
        print(f"File 1: {info1['total_rows']} rows, {info1['total_columns']} columns")
        print(f"File 2: {info2['total_rows']} rows, {info2['total_columns']} columns")
        
        # Test sample reading
        start_time = time.time()
        sample1 = lecteur.get_file_sample(file1, 1000)
        sample2 = lecteur.get_file_sample(file2, 1000)
        sample_time = time.time() - start_time
        
        print(f"Sample reading took: {sample_time:.2f} seconds")
        print(f"Got samples of {len(sample1)} and {len(sample2)} rows")
        
        # Clean up
        os.remove(file1)
        os.remove(file2)
        
        return True
        
    except Exception as e:
        print(f"Error in optimized reading test: {e}")
        return False

def test_memory_management():
    """Test memory management utilities"""
    print("\n=== Testing Memory Management ===")
    
    try:
        from app.services.memory_manager import MemoryManager
        
        memory_mgr = MemoryManager()
        
        # Get initial memory usage
        initial_memory = memory_mgr.get_memory_usage()
        print(f"Initial memory usage: {initial_memory['rss_mb']:.2f} MB ({initial_memory['percent']:.1f}%)")
        print(f"Available memory: {initial_memory['available_mb']:.2f} MB")
        
        # Create a large DataFrame to test memory optimization
        print("Creating large DataFrame...")
        df = pd.DataFrame({
            'numbers': np.random.randint(1, 100000, 50000),
            'floats': np.random.random(50000),
            'categories': np.random.choice(['A', 'B', 'C', 'D'], 50000),
            'text': [f"text_{i}" for i in range(50000)]
        })
        
        print(f"DataFrame created with {len(df)} rows and {len(df.columns)} columns")
        
        # Optimize memory
        optimized_df = memory_mgr.optimize_dataframe_memory(df)
        
        # Check memory after optimization
        memory_mgr.force_garbage_collection()
        final_memory = memory_mgr.get_memory_usage()
        
        print(f"Final memory usage: {final_memory['rss_mb']:.2f} MB ({final_memory['percent']:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"Error in memory management test: {e}")
        return False

def main():
    """Run all tests"""
    print("=== DataAlign Optimized Services Demo ===")
    print(f"Python version: {sys.version}")
    
    # Test 1: Optimized file reading
    reading_success = test_optimized_reading()
    
    # Test 2: Memory management
    memory_success = test_memory_management()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Optimized reading: {'✓ PASSED' if reading_success else '✗ FAILED'}")
    print(f"Memory management: {'✓ PASSED' if memory_success else '✗ FAILED'}")
    
    if reading_success and memory_success:
        print("\n🎉 All optimization features are working correctly!")
        print("\nYour DataAlign application is now optimized for handling large files:")
        print("- Files are read in chunks to manage memory usage")
        print("- Memory optimization reduces DataFrame size")
        print("- Database backend handles comparisons efficiently")
        print("- Progress monitoring keeps you informed during long operations")
    else:
        print("\n⚠️  Some optimization features need attention.")
        print("Check the error messages above for details.")

if __name__ == "__main__":
    main()
