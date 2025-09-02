#!/usr/bin/env python3
"""Quick verification of GPT integration"""

print("🔍 DataAlign GPT-4 Integration Verification")
print("=" * 45)

# Step 1: Check if dotenv works
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ python-dotenv imported and loaded")
except Exception as e:
    print(f"❌ dotenv error: {e}")
    exit(1)

# Step 2: Check environment variables
import os
api_key = os.getenv('OPENAI_API_KEY')
gpt_enabled = os.getenv('ENABLE_GPT_PROCESSING')

print(f"🔑 API Key: {'SET' if api_key and len(api_key) > 20 else 'NOT SET'}")
print(f"🤖 GPT Enabled: {gpt_enabled}")

# Step 3: Test OpenAI import
try:
    import openai
    print("✅ OpenAI package imported")
except Exception as e:
    print(f"❌ OpenAI import error: {e}")

# Step 4: Test our GPT processor
try:
    import sys
    sys.path.append('app')
    from app.services.gpt_data_processor import GPTDataProcessor
    print("✅ GPTDataProcessor imported")
    
    # Test initialization
    if api_key and len(api_key) > 20:
        processor = GPTDataProcessor()
        print("✅ GPTDataProcessor initialized")
        
        # Test with sample data to verify DataFrame structure is maintained
        import pandas as pd
        sample_df = pd.DataFrame({
            'Name': ['John Doe', 'jane smith'],
            'Amount': ['$1,000', '2000'],
            'Date': ['2024-01-15', '15/01/2024']
        })
        
        print("📊 Testing data cleaning...")
        cleaned_df = processor.clean_data_chunk(sample_df)
        print(f"   Original columns: {list(sample_df.columns)}")
        print(f"   Cleaned columns: {list(cleaned_df.columns)}")
        print(f"   Structure preserved: {'✅' if len(cleaned_df.columns) == len(sample_df.columns) else '❌'}")
        
    else:
        print("⚠️  API key needed for full GPT testing")
        
except Exception as e:
    print(f"❌ GPT processor error: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 Integration Status:")
if api_key and len(api_key) > 20:
    print("✅ Ready for GPT-4 enhanced file processing!")
    print("   Run: python start_with_gpt.py")
else:
    print("⚠️  Set OPENAI_API_KEY in .env to enable GPT-4")

print("\n💡 Next steps:")
print("1. Verify your .env file has the correct API key")
print("2. Start the application: python start_with_gpt.py")
print("3. Test GPT features in the Fast Test modal")
