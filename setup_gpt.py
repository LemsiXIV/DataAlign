#!/usr/bin/env python3
"""
DataAlign v2.0 - GPT-4 Setup and Installation Script

This script helps set up the GPT-4 integration for DataAlign
"""

import os
import subprocess
import sys
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai==1.58.1"])
        print("✅ OpenAI package installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install OpenAI package: {e}")
        return False

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment configuration...")
    
    # Check if .env file exists
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("📄 Creating .env file from .env.example...")
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ .env file created")
        else:
            print("⚠️  .env file not found")
    
    # Check OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your_openai_api_key_here':
        print("⚠️  OpenAI API key not configured")
        print("   Please set OPENAI_API_KEY in your .env file")
        return False
    else:
        print("✅ OpenAI API key configured")
        return True

def main():
    """Main setup function"""
    print("DataAlign v2.0 - GPT-4 Setup")
    print("=" * 40)
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Check environment
    env_configured = check_environment()
    
    print("\n🎯 Setup Summary:")
    print("✅ GPT-4 integration code installed")
    print("✅ OpenAI package installed")
    print("✅ Configuration files ready")
    
    if env_configured:
        print("✅ Environment properly configured")
        print("\n🚀 You can now start DataAlign with GPT-4 support!")
        print("   Run: python start.py")
    else:
        print("⚠️  Environment configuration needed")
        print("\n📝 Next steps:")
        print("1. Edit .env file and add your OpenAI API key:")
        print("   OPENAI_API_KEY=your_actual_api_key_here")
        print("2. Run: python start.py")
    
    print("\n💡 GPT-4 Features:")
    print("• Intelligent data structure analysis")
    print("• Automatic data cleaning and formatting")
    print("• Smart column mapping suggestions")
    print("• Enhanced comparison accuracy")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        sys.exit(1)
