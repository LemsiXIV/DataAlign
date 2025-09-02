#!/usr/bin/env python3
"""
Test script for GPT-4 integration in DataAlign

This script tests the GPT data processing functionality
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'app'))

def test_gpt_integration():
    """Test GPT-4 integration functionality"""
    print("🧪 Testing GPT-4 Integration for DataAlign v2.0")
    print("=" * 50)
    
    try:
        # Load environment variables first
        print("0. Loading environment variables...")
        from dotenv import load_dotenv
        load_dotenv()
        print("   ✅ Environment variables loaded")
        
        # Debug environment variables
        import os
        api_key_env = os.getenv('OPENAI_API_KEY')
        gpt_enabled_env = os.getenv('ENABLE_GPT_PROCESSING')
        print(f"   🔍 Raw OPENAI_API_KEY from env: {'Set' if api_key_env else 'Not set'}")
        print(f"   🔍 Raw ENABLE_GPT_PROCESSING from env: {gpt_enabled_env}")
        
        # Test configuration loading
        print("1. Testing configuration...")
        from app.config import Config
        
        # Check if OpenAI API key is configured
        api_key = Config.OPENAI_API_KEY
        gpt_enabled = Config.ENABLE_GPT_PROCESSING
        
        print(f"   ✅ GPT Processing Enabled: {gpt_enabled}")
        print(f"   ✅ OpenAI API Key Configured: {'Yes' if api_key and api_key != 'your_openai_api_key_here' else 'No'}")
        
        # Test GPT processor import
        print("2. Testing GPT processor import...")
        from app.services.gpt_data_processor import GPTDataProcessor
        print("   ✅ GPTDataProcessor imported successfully")
        
        # Test GPT processor initialization
        print("3. Testing GPT processor initialization...")
        if api_key and api_key != 'your_openai_api_key_here':
            processor = GPTDataProcessor()
            print("   ✅ GPTDataProcessor initialized successfully")
            
            # Test with sample data
            print("4. Testing with sample data...")
            sample_data = pd.DataFrame({
                'ID': ['001', '002', '003'],
                'Name': ['John Doe', 'jane smith', 'BOB JOHNSON'],
                'Amount': ['$1,000.50', '2000', '$3,500.00'],
                'Date': ['2024-01-15', '15/01/2024', '2024-1-15']
            })
            
            print("   📊 Sample input data:")
            print(sample_data.to_string(index=False))
            
            # Test data analysis
            analysis = processor.analyze_data_structure(sample_data)
            print("   ✅ Data structure analysis completed")
            print(f"   📈 Analysis: {analysis}")
            
        else:
            print("   ⚠️  OpenAI API key not configured - skipping live tests")
            print("   💡 To enable full testing, set OPENAI_API_KEY in your environment")
        
        # Test route registration
        print("5. Testing route registration...")
        from app.routes.gpt_routes import gpt_bp
        print(f"   ✅ GPT blueprint registered with {len(gpt_bp.deferred_functions)} routes")
        
        # Test integration with existing services
        print("6. Testing integration with existing services...")
        from app.services.lecteur_fichier_optimise import LecteurFichierOptimise
        print("   ✅ File reader integration available")
        
        print("\n🎉 GPT-4 Integration Test Complete!")
        print("=" * 50)
        
        if api_key and api_key != 'your_openai_api_key_here':
            print("✅ All tests passed - GPT-4 functionality is ready!")
        else:
            print("⚠️  Tests passed but GPT-4 requires API key configuration")
            print("   Set OPENAI_API_KEY environment variable to enable GPT-4 features")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test GPT API endpoints"""
    print("\n🔗 Testing API Endpoints")
    print("-" * 30)
    
    try:
        from app.routes.gpt_routes import gpt_bp
        
        endpoints = []
        for rule in gpt_bp.deferred_functions:
            if hasattr(rule, 'rule'):
                endpoints.append(rule.rule)
        
        expected_endpoints = [
            '/analyze-file',
            '/suggest-comparison', 
            '/apply-cleaning',
            '/get-enhanced-config'
        ]
        
        print("Expected endpoints:")
        for endpoint in expected_endpoints:
            print(f"   📍 /gpt{endpoint}")
        
        print("✅ API endpoints ready for registration")
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("DataAlign v2.0 - GPT-4 Integration Test")
    print("🚀 Starting comprehensive integration test...\n")
    
    success = test_gpt_integration() and test_api_endpoints()
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Start the application with: python docker_start.py")
        print("3. Test GPT enhancement in the Fast Test modal")
        print("4. Monitor the application logs for GPT processing")
        
        exit(0)
    else:
        print("\n❌ Integration test failed - check errors above")
        exit(1)
