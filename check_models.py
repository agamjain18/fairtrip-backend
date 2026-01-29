import google.generativeai as genai
import os

API_KEY = "AIzaSyBm_cgJs_C7sQ8MUdtE9ly5wGq3LRuBLNI"
genai.configure(api_key=API_KEY)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
