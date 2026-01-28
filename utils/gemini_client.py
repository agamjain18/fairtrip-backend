import google.generativeai as genai
import os
import time
import random

# Pool of API Keys to distribute load
API_KEYS = [
    "AIzaSyBm_cgJs_C7sQ8MUdtE9ly5wGq3LRuBLNI", # Original
    "AIzaSyBgnH9SH_bK-kMhqCK0Pr19f5LVLdQ4rFo",
    "AIzaSyBNk52xU3t_euTQb1jY0Tdqz9w_XWCiKig",
    "AIzaSyBijvOxdx0ysGDIBTAAYZ57y-cPKhuXVJw",
    "AIzaSyBNfScHvLVwlUoS0xp86kv_WgLe9B71_fg",
    "AIzaSyDKWeizqNRRCHBoMzHSaD6oyVc-hweQ7KY",
    "AIzaSyBlRuDq-uBoZQETuqWibwU9ymHULryHxJA",
    "AIzaSyAaEQWIhWAznrYqSLpGnNfgeX-LZvgqTd8"
]

# List of models to try in order of preference
FALLBACK_MODELS = [
    'gemini-2.0-flash',
    'gemini-1.5-flash',
    'gemini-1.5-flash-latest',
    'gemini-1.5-pro',
    'gemini-pro',
    'gemini-flash-latest'
]

def get_random_api_key():
    return random.choice(API_KEYS)

def generate_content_with_fallback(contents, generation_config=None):
    """
    Attempts to generate content using a list of fallback models and rotating API keys.
    
    Args:
        contents: The prompt or list of [prompt, image] to send.
        generation_config: Optional generation configuration.
        
    Returns:
        The generation response.
        
    Raises:
        Exception: If all models fail.
    """
    last_error = None
    
    for model_name in FALLBACK_MODELS:
        try:
            # Rotate API Key for each attempt to handle rate limits/quotas
            current_key = get_random_api_key()
            genai.configure(api_key=current_key)
            
            print(f"🤖 Trying Gemini Model: {model_name} with key ...{current_key[-4:]}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(contents, generation_config=generation_config)
            print(f"✅ Success with {model_name}")
            return response
        except Exception as e:
            print(f"⚠️ Failed with {model_name}: {e}")
            last_error = e
            time.sleep(1) # Brief pause before next attempt
            continue
            
    raise Exception(f"All Gemini models failed. Last error: {last_error}")
