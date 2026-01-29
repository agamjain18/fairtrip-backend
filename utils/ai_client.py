import os
import time
import random
from groq import Groq

# Groq API Key
API_KEY = "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"

# Initialize Groq client
client = Groq(api_key=API_KEY)

# List of models to try in order of preference
FALLBACK_MODELS = [
    'llama-3.3-70b-versatile',
    'llama-3.1-70b-versatile',
    'mixtral-8x7b-32768',
    'gemma2-9b-it'
]

class AIResponse:
    def __init__(self, text):
        self.text = text

def generate_content_with_fallback(contents, generation_config=None):
    """
    Attempts to generate content using Groq with fallback models.
    
    Args:
        contents: The prompt string. (Multimedia not supported directly in this wrapper yet)
        generation_config: Optional config (ignored for now in simple wrapper).
        
    Returns:
        AIResponse object with .text attribute.
    """
    # Create prompt from contents
    prompt = ""
    if isinstance(contents, list):
        # Join text parts, ignore non-text (files) for now, assuming caller handles text extraction
        for item in contents:
            if isinstance(item, str):
                prompt += item + "\n"
    else:
        prompt = str(contents)

    last_error = None
    
    for model_name in FALLBACK_MODELS:
        try:
            print(f"🤖 Trying Groq Model: {model_name}...")
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=model_name,
                temperature=0.7,
            )
            
            result_text = chat_completion.choices[0].message.content
            print(f"✅ Success with {model_name}")
            return AIResponse(result_text)
            
        except Exception as e:
            print(f"⚠️ Failed with {model_name}: {e}")
            last_error = e
            time.sleep(1) # Brief pause before next attempt
            continue
            
    raise Exception(f"All AI models failed. Last error: {last_error}")
