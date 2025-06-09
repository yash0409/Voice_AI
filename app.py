import os
import re
import requests
import tempfile
import speech_recognition as sr
from gtts import gTTS
from deep_translator import GoogleTranslator
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
import av

# 🔑 OpenRouter API Key
OPENROUTER_API_KEY = st.secrets["openrouter_api_key"]

# 🎤 Audio Processor for WebRTC
class AudioProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.transcript = ""

    def recv(self, frame: av.AudioFrame):
        audio_data = frame.to_ndarray().flatten().tobytes()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            with sr.AudioFile(temp_path) as source:
                audio = self.recognizer.record(source)
                self.transcript = self.recognizer.recognize_google(audio, language="hi-IN")
        except sr.UnknownValueError:
            self.transcript = ""
        except sr.RequestError as e:
            self.transcript = f"Speech API error: {e}"
        finally:
            os.remove(temp_path)
        return None

# 🔁 Get AI Response
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
            return "माफ़ कीजिए, मैं जवाब नहीं दे पाया।"
    except Exception as e:
        st.error(f"API Exception: {e}")
        return "माफ़ कीजिए, कुछ गलती हो गई।"

# 🌍 Translate
def translate_text(text, target_lang):
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception as e:
        st.error(f"Translation failed: {e}")
        return text

# 🧹 Clean text
def clean_text(text, lang_code):
    unicode_blocks = {
        'ta': r'\u0B80-\u0BFF',  # Tamil
        'bn': r'\u0980-\u09FF',
        'mr': r'\u0900-\u097F',
        'hi': r'\u0900-\u097F',
        'te': r'\u0C00-\u0C7F',
        'gu': r'\u0A80-\u0AFF',
        'kn': r'\u0C80-\u0CFF',
        'ml': r'\u0D00-\u0D7F',
        'pa': r'\u0A00-\u0A7F'
    }
    pattern = unicode_blocks.get(lang_code, r'\u0000-\uFFFF')
    return re.sub(rf'[^\s{pattern}.,!?]', '', text)

# 🔊 TTS
def speak(text, lang_code):
    cleaned = clean_text(text, lang_code)
    tts = gTTS(text=cleaned, lang=lang_code)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        path = fp.name
    try:
        tts.save(path)
        audio_file = open(path, 'rb')
        st.audio(audio_file.read(), format='audio/mp3')
        audio_file.close()
    except Exception as e:
        st.error(f"TTS failed: {e}")
    finally:
        if os.path.exists(path):
            os.remove(path)

# 🏷 Language code
def language_code(region):
    codes = {
        'Tamil': 'ta',
        'Bengali': 'bn',
        'Marathi': 'mr',
        'Hindi': 'hi',
        'Telugu': 'te',
        'Gujarati': 'gu',
        'Kannada': 'kn',
        'Malayalam': 'ml',
        'Punjabi': 'pa'
    }
    return codes.get(region, 'hi')

# 🌐 Streamlit UI
st.set_page_config(page_title="🎙️ Voice AI Translator", layout="centered")
st.title("🧠🎤 Voice AI Assistant")
st.markdown("Speak in **Hindi**, get AI response, and hear it in a selected **regional language**.")

regional_language = st.selectbox("🌐 Select Regional Language", [
    'Hindi', 'Tamil', 'Bengali', 'Marathi', 'Telugu',
    'Gujarati', 'Kannada', 'Malayalam', 'Punjabi'
])
lang_code = language_code(regional_language)

# 🎙️ WebRTC Audio Recorder
st.subheader("🎙 Click below and speak in Hindi")
ctx = webrtc_streamer(
    key="speech",
    mode=WebRtcMode.SENDONLY,
    in_audio=True,
    client_settings=ClientSettings(
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    ),
    audio_processor_factory=AudioProcessor,
    async_processing=True,
)

# 📥 Process recognized text
if ctx and ctx.state.audio_processor:
    processor = ctx.state.audio_processor
    if processor.transcript:
        st.success(f"📝 आपने कहा: {processor.transcript}")
        response = get_ai_response_openrouter(processor.transcript)
        st.text(f"🤖 AI (Hindi): {response}")

        translated = translate_text(response, lang_code)
        st.text(f"🌍 Translated ({regional_language}): {translated}")
        speak(translated, lang_code)