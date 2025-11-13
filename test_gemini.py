#!/usr/bin/env python3
"""
Test script to verify Gemini API key and available models
"""

from dotenv import load_dotenv, find_dotenv
import os
import google.generativeai as genai

def test_gemini_api():
    """Test the Gemini API key and list available models"""
    
    # Load environment variables
    load_dotenv(find_dotenv())
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    print("=== Gemini API Test ===")
    print(f"API Key loaded: {'Yes' if GEMINI_API_KEY else 'No'}")
    
    if GEMINI_API_KEY:
        print(f"API Key length: {len(GEMINI_API_KEY)} characters")
        print(f"API Key preview: {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-4:]}")
    else:
        print("❌ No API key found in environment variables")
        return False
    
    try:
        # Configure the API key
        genai.configure(api_key=GEMINI_API_KEY)
        print("✅ API key configured successfully")
        
        # List available models
        print("\n=== Available Models ===")
        models = genai.list_models()
        
        for model in models:
            print(f"Model: {model.name}")
            print(f"  Display Name: {model.display_name}")
            print(f"  Supported Methods: {model.supported_generation_methods}")
            print("---")
        
        # Test a simple generation
        print("\n=== Testing Simple Generation ===")
        model_names_to_test = [
            "gemini-flash-latest",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-pro-latest"
        ]
        
        for model_name in model_names_to_test:
            try:
                print(f"Testing model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Say hello")
                print(f"✅ {model_name}: {response.text[:50]}...")
                break
            except Exception as e:
                print(f"❌ {model_name}: {str(e)}")
                continue
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_gemini_api()
    if not success:
        print("\n🔧 Troubleshooting Tips:")
        print("1. Make sure your GEMINI_API_KEY is complete and valid")
        print("2. Get a new API key from: https://makersuite.google.com/app/apikey")
        print("3. Ensure the API key has the necessary permissions")
        print("4. Check if your API quota/billing is set up correctly")
