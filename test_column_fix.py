#!/usr/bin/env python3
"""
Test the file upload and column selection without full GPT API calls
"""

import pandas as pd
import sys
import os

# Add app to path
sys.path.append('app')

from dotenv import load_dotenv
load_dotenv()

def test_data_processing():
    """Test that our fixed GPT processor maintains DataFrame structure"""
    
    print("🧪 Testing Data Processing Fix")
    print("=" * 35)
    
    try:
        from app.services.gpt_data_processor import GPTDataProcessor
        
        # Create sample data that might cause issues
        test_data = pd.DataFrame({
            'ID': ['001', '002', '003'],
            'Customer Name': ['John Doe', ' jane smith ', 'BOB JOHNSON'],
            'Amount': ['$1,000.50', '2000', '$3,500.00'],
            'Purchase Date': ['2024-01-15', '15/01/2024', '2024-1-15'],
            'Status': ['active', 'PENDING', 'completed ']
        })
        
        print("📊 Original data structure:")
        print(f"   Columns: {list(test_data.columns)}")
        print(f"   Shape: {test_data.shape}")
        print(f"   Sample row: {test_data.iloc[0].to_dict()}")
        
        # Initialize processor
        processor = GPTDataProcessor()
        
        # Clean the data (should maintain structure)
        cleaned_data = processor.clean_data_chunk(test_data)
        
        print("\n✨ After cleaning:")
        print(f"   Columns: {list(cleaned_data.columns)}")
        print(f"   Shape: {cleaned_data.shape}")
        print(f"   Sample row: {cleaned_data.iloc[0].to_dict()}")
        
        # Verify structure is maintained
        structure_ok = (
            len(cleaned_data.columns) == len(test_data.columns) and
            list(cleaned_data.columns) == list(test_data.columns) and
            cleaned_data.shape[0] == test_data.shape[0]
        )
        
        print(f"\n🎯 Structure preserved: {'✅ YES' if structure_ok else '❌ NO'}")
        
        if structure_ok:
            print("✅ Fix successful! Column selection should work properly now.")
            print("   The GPT enhancement will clean data without breaking structure.")
        else:
            print("❌ Issue still exists - structure was modified")
            
        return structure_ok
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_column_selection_simulation():
    """Simulate the column selection process"""
    
    print("\n🎮 Simulating Column Selection Process")
    print("=" * 40)
    
    # Simulate two files with different structures
    file1_data = pd.DataFrame({
        'customer_id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'order_date': ['2024-01-01', '2024-01-02', '2024-01-03']
    })
    
    file2_data = pd.DataFrame({
        'id': [1, 2, 3],
        'customer_name': ['Alice Smith', 'Bob Jones', 'Charlie Brown'],
        'date': ['2024-01-01', '2024-01-02', '2024-01-03']
    })
    
    print("📁 File 1 columns for selection:")
    for i, col in enumerate(file1_data.columns):
        print(f"   {i+1}. {col}")
    
    print("\n📁 File 2 columns for selection:")
    for i, col in enumerate(file2_data.columns):
        print(f"   {i+1}. {col}")
    
    print("\n✅ This is what users should see in the 'Choisissez les clés' interface")
    return True

if __name__ == "__main__":
    print("DataAlign - Column Selection Fix Test")
    print("====================================\n")
    
    # Test 1: Data processing
    test1_ok = test_data_processing()
    
    # Test 2: Column selection simulation
    test2_ok = test_column_selection_simulation()
    
    print(f"\n🏁 Overall Result: {'✅ FIXED' if test1_ok and test2_ok else '❌ NEEDS MORE WORK'}")
    
    if test1_ok and test2_ok:
        print("\n🚀 Ready to test in the application!")
        print("1. Start the app: python start_with_gpt.py")
        print("2. Upload files in Fast Test")
        print("3. Check if columns appear separately in selection")
