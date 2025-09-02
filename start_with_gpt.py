#!/usr/bin/env python3
"""
DataAlign v2.0 Startup Script with GPT-4 Integration
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

def check_gpt_configuration():
    """Check if GPT-4 is properly configured"""
    print("🔍 Checking GPT-4 Configuration...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    gpt_enabled = os.getenv('ENABLE_GPT_PROCESSING', 'false').lower() == 'true'
    
    print(f"   🔑 OpenAI API Key: {'✅ Configured' if api_key and api_key != 'your_openai_api_key_here' else '❌ Not configured'}")
    print(f"   🤖 GPT Processing: {'✅ Enabled' if gpt_enabled else '❌ Disabled'}")
    
    return api_key and gpt_enabled

def start_application():
    """Start the DataAlign application"""
    print("\n🚀 Starting DataAlign v2.0 with GPT-4 Integration...")
    
    # Check configuration first
    gpt_ready = check_gpt_configuration()
    
    if gpt_ready:
        print("   ✅ GPT-4 features will be available")
    else:
        print("   ⚠️  GPT-4 features will be disabled")
        print("   💡 To enable: Set OPENAI_API_KEY and ENABLE_GPT_PROCESSING=true in .env")
    
    print("\n📍 Starting Flask application...")
    
    # Start the Flask app
    try:
        from app import create_app
        app = create_app()
        
        print("✅ Application initialized successfully!")
        print("\n🌐 Access your application at:")
        print("   Local:    http://localhost:5000")
        print("   Network:  Check your local IP address")
        print("\n🎯 GPT-4 Features Available:")
        if gpt_ready:
            print("   • Fast Test with AI enhancement")
            print("   • Intelligent data cleaning")
            print("   • Smart column mapping")
            print("   • API endpoints at /gpt/*")
        else:
            print("   • Configure OPENAI_API_KEY to enable GPT-4 features")
        
        print("\n🛑 Press Ctrl+C to stop the server")
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except KeyboardInterrupt:
        print("\n\n👋 DataAlign server stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start application: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("DataAlign v2.0 - Enhanced with GPT-4 AI Processing")
    print("=" * 55)
    start_application()
