import requests
import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import tempfile
import os

# OpenRouter API key from Streamlit secrets
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
            st.error(f"API Error: {response.status_code} - {response.text}")
            return "Sorry, I couldn't get a response."
    except Exception as e:
        st.error(f"API Exception: {e}")
        return "Sorry, something went wrong."

# Function to translate text to target language
def translate_text(text, target_lang):
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception as e:
        st.error(f"Translation failed: {e}")
        return text

# Function to play TTS audio from text
def speak(text, lang_code):
    try:
        tts = gTTS(text=text, lang=lang_code)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
        tts.save(temp_path)
        audio_file = open(temp_path, 'rb')
        audio_bytes = audio_file.read()
        audio_file.close()
        st.audio(audio_bytes, format='audio/mp3')
    except Exception as e:
        st.error(f"TTS failed: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# Mapping from language names to codes (gTTS and GoogleTranslator compatible)
LANGUAGE_CODES = {
    'Hindi': 'hi',
    'Tamil': 'ta',
    'Bengali': 'bn',
    'Marathi': 'mr',
    'Telugu': 'te',
    'Gujarati': 'gu',
    'Kannada': 'kn',
    'Malayalam': 'ml',
    'Punjabi': 'pa'
}

# Streamlit UI
st.set_page_config(page_title="Simple Voice AI Chatbot", layout="centered")
st.title("🧠 Simple AI Chatbot")

# User input
user_input = st.text_input("Enter your message in Hindi or English:")

# Language selection for translation & TTS
target_language = st.selectbox("Select language for AI response & speech", list(LANGUAGE_CODES.keys()))
lang_code = LANGUAGE_CODES[target_language]

if st.button("Send"):
    if user_input.strip() == "":
        st.warning("Please enter a message.")
    else:
        # Get AI response
        ai_response = get_ai_response_openrouter(user_input)
        st.text_area("🤖 AI Response:", value=ai_response, height=150)

        # Translate AI response
        translated_text = translate_text(ai_response, lang_code)
        st.text_area(f"🌍 Translated ({target_language}):", value=translated_text, height=150)

        # Play TTS audio of translated response
        speak(translated_text, lang_code)
