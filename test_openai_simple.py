#!/usr/bin/env python3
"""
Simple test to verify OpenAI API is working with new syntax
"""

import os
import sys
sys.path.append('app')

from dotenv import load_dotenv
load_dotenv()

def test_openai_api():
    """Test basic OpenAI API functionality"""
    
    print("🔍 Testing OpenAI API Connection")
    print("=" * 35)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your_openai_api_key_here':
        print("❌ OpenAI API key not configured")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        import openai
        
        # Initialize client with new syntax
        client = openai.OpenAI(api_key=api_key)
        
        print("✅ OpenAI client initialized")
        
        # Test simple API call
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond with only 'API_TEST_SUCCESS'."},
                {"role": "user", "content": "Test message"}
            ],
            max_tokens=10,
            temperature=0.1,
        )
        
        result = response.choices[0].message.content
        print(f"✅ API Response: {result}")
        
        if "API_TEST_SUCCESS" in result:
            print("🎉 OpenAI API is working correctly!")
            return True
        else:
            print("⚠️ API working but unexpected response")
            return True
            
    except Exception as e:
        print(f"❌ API Error: {e}")
        return False

def test_delimiter_detection():
    """Test delimiter detection with GPT"""
    
    print("\n🔍 Testing GPT Delimiter Detection")
    print("=" * 37)
    
    try:
        from app.services.gpt_data_processor import GPTDataProcessor
        
        # Create simple test content
        test_content = "Id;Name;Email\n1;John;john@test.com\n2;Jane;jane@test.com"
        
        # Write to temp file
        os.makedirs("temp", exist_ok=True)
        with open("temp/simple_test.csv", "w") as f:
            f.write(test_content)
        
        print("📝 Test file created with semicolon delimiters")
        
        # Test GPT analysis
        processor = GPTDataProcessor()
        analysis = processor.analyze_and_fix_file_structure("temp/simple_test.csv")
        
        print(f"🤖 GPT Analysis:")
        print(f"   Detected delimiter: '{analysis.get('detected_delimiter', 'N/A')}'")
        print(f"   Detected encoding: {analysis.get('detected_encoding', 'N/A')}")
        print(f"   Issues found: {analysis.get('structure_issues', [])}")
        
        # Test fixing
        fixed_df = processor.fix_file_with_gpt_analysis("temp/simple_test.csv")
        print(f"✅ Fixed structure: {len(fixed_df.columns)} columns")
        print(f"   Columns: {list(fixed_df.columns)}")
        
        # Clean up
        os.remove("temp/simple_test.csv")
        
        return len(fixed_df.columns) > 1
        
    except Exception as e:
        print(f"❌ Delimiter test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 OpenAI API & Delimiter Detection Test")
    print("========================================\n")
    
    # Test API connection
    api_works = test_openai_api()
    
    if api_works:
        # Test delimiter detection
        delimiter_works = test_delimiter_detection()
        
        print(f"\n🏁 Final Results:")
        print(f"   API Connection: {'✅ SUCCESS' if api_works else '❌ FAILED'}")
        print(f"   Delimiter Detection: {'✅ SUCCESS' if delimiter_works else '❌ FAILED'}")
        
        if api_works and delimiter_works:
            print("\n🎉 GPT-4 is ready to fix your semicolon delimiter issues!")
        else:
            print("\n❌ Some issues remain - check the errors above")
            
    else:
        print("\n❌ Cannot test delimiter detection without working API")
