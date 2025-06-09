import requests
import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import tempfile
import os

# OpenRouter API key from secrets
OPENROUTER_API_KEY = st.secrets["openrouter_api_key"]

# Function to get AI response from OpenRouter
def get_ai_response_openrouter(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "meta-llama/llama-3-8b-instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that replies in simple language."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            st.error(f"API Error: {response.status_code}")
            return "Sorry, I couldn't get a response."
    except Exception as e:
        st.error(f"API Exception: {e}")
        return "Sorry, something went wrong."

# Optional: translate text
def translate_text(text, target_lang):
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception as e:
        st.error(f"
