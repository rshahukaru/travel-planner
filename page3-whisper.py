# page3-whisper.py
import streamlit as st
from openai import OpenAI
import os
from audio_recorder_streamlit import audio_recorder
import base64
import time

# Dictionary of countries and their primary languages
COUNTRY_LANGUAGES = {
    "Spain": "Spanish",
    "France": "French",
    "Germany": "German",
    "Italy": "Italian",
    "Japan": "Japanese",
    "China": "Chinese",
    "Brazil": "Portuguese",
    "North India": "Hindi",
    "Telangana / Andhra Pradesh": "Telugu",
}

class TranslatorPage:
    def __init__(self):
        self.setup_session_state()
        self.setup_openai_client()
        self.cleanup_audio_files()

    def setup_session_state(self):
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'last_recorded_audio' not in st.session_state:
            st.session_state.last_recorded_audio = None
        if 'target_language' not in st.session_state:
            st.session_state.target_language = None

    def setup_openai_client(self):
        if 'openai_client' not in st.session_state:
            api_key = st.secrets["openai_api_key"]
            st.session_state.openai_client = OpenAI(api_key=api_key)

    def cleanup_audio_files(self):
        try:
            for file in os.listdir():
                if (file.startswith("audio_input_") or file.startswith("audio_response_")) and file.endswith(".mp3"):
                    try:
                        os.remove(file)
                    except Exception as e:
                        st.warning(f"Could not remove audio file {file}: {str(e)}")
        except Exception as e:
            st.warning(f"Error during audio cleanup: {str(e)}")

    def transcribe_audio(self, audio_path):
        with open(audio_path, "rb") as audio_file:
            transcript = st.session_state.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return transcript.text

    def text_to_audio(self, text, audio_path, voice="nova"):
        response = st.session_state.openai_client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        response.stream_to_file(audio_path)

    def auto_play_audio(self, audio_file):
        if os.path.exists(audio_file):
            with open(audio_file, "rb") as f:
                audio_bytes = f.read()
            base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
            audio_html = f'<audio src="data:audio/mp3;base64,{base64_audio}" controls autoplay>'
            st.markdown(audio_html, unsafe_allow_html=True)

    def translate_text(self, text, target_language):
        messages = [
            {"role": "system", "content": f"You are a translator. Translate the following text to {target_language}. Maintain the tone and meaning of the original text. Only respond with the translation, no additional text. Also, do not talk too fast"},
            {"role": "user", "content": text}
        ]
        
        response = st.session_state.openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.75
        )
        
        return response.choices[0].message.content

    def process_input(self, text, target_language, is_voice=False):
        translated_text = self.translate_text(text, target_language)
        
        if is_voice:
            audio_file = f"audio_response_{int(time.time())}.mp3"
            self.text_to_audio(translated_text, audio_file)
            return translated_text, audio_file
        
        return translated_text, None

    def run(self):
        st.title("Travel Translation Assistant")

        # Country/Language Selection
        st.sidebar.header("Translation Settings")
        country_selection = st.sidebar.selectbox(
            "Where are you traveling to?",
            options=list(COUNTRY_LANGUAGES.keys()),
            key="country_selection"
        )
        
        # Update target language based on country selection
        st.session_state.target_language = COUNTRY_LANGUAGES[country_selection]
        st.sidebar.write(f"Translation will be provided in: {st.session_state.target_language}")

        # Chat interface
        chat_container = st.container()

        # Display chat history
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
                    if "translation" in message:
                        st.write(f"🔄 {message['translation']}")
                    if "audio" in message:
                        self.auto_play_audio(message["audio"])

        # Voice and text input
        col1, col2 = st.columns([8, 2])
        
        with col2:
            recorded_audio = audio_recorder(
                text="",
                recording_color="#e74c3c",
                neutral_color="#95a5a6",
                key="voice_recorder"
            )

        with col1:
            text_input = st.chat_input("Type your message or use voice input...")

        # Handle text input
        if text_input:
            translation, _ = self.process_input(text_input, st.session_state.target_language)
            
            st.session_state.messages.append({
                "role": "user",
                "content": text_input,
                "translation": translation
            })
            st.rerun()

        # Handle voice input
        if recorded_audio is not None and recorded_audio != st.session_state.last_recorded_audio:
            st.session_state.last_recorded_audio = recorded_audio
            
            # Save and transcribe audio
            audio_file = f"audio_input_{int(time.time())}.mp3"
            with open(audio_file, "wb") as f:
                f.write(recorded_audio)

            # Transcribe the audio
            transcribed_text = self.transcribe_audio(audio_file)
            os.remove(audio_file)

            # Get translation and audio response
            translation, response_audio = self.process_input(
                transcribed_text, 
                st.session_state.target_language, 
                is_voice=True
            )

            # Update chat history
            st.session_state.messages.append({
                "role": "user",
                "content": f"🎤 {transcribed_text}",
                "translation": translation,
                "audio": response_audio
            })
            
            st.rerun()

def main():
    translator = TranslatorPage()
    translator.run()

if __name__ == "__main__":
    main()