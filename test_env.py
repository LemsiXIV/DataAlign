#!/usr/bin/env python3
"""Simple environment test"""

from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Check environment variables
api_key = os.getenv('OPENAI_API_KEY')
gpt_enabled = os.getenv('ENABLE_GPT_PROCESSING')

print("Environment Test Results:")
print(f"OPENAI_API_KEY: {'SET' if api_key else 'NOT SET'}")
print(f"ENABLE_GPT_PROCESSING: {gpt_enabled}")

if api_key:
    print(f"API Key starts with: {api_key[:10]}...")
else:
    print("No API key found")

# Check .env file exists
env_file_exists = os.path.exists('.env')
print(f".env file exists: {env_file_exists}")

if env_file_exists:
    with open('.env', 'r') as f:
        content = f.read()
        print(f".env file content preview: {content[:100]}...")
