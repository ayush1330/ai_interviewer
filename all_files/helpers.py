import base64
import streamlit as st
import os
import openai
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)
openai.api_key = api_key


def speech_to_text(audio_data):
    with open(audio_data, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", response_format="text", file=audio_file
        )
    return transcript


def text_to_speech(input_text):
    # Check if input text is too long
    if len(input_text) > 4000:
        print(
            f"Warning: Input text is very long ({len(input_text)} chars). Truncating to 4000 chars."
        )
        input_text = input_text[:4000]

    try:
        print(f"Generating speech for text of length: {len(input_text)}")
        response = client.audio.speech.create(
            model="tts-1", voice="nova", input=input_text
        )

        # Create a unique filename based on timestamp
        timestamp = int(time.time())
        webm_file_path = f"temp_audio_{timestamp}.mp3"

        print(f"Writing audio to file: {webm_file_path}")
        with open(webm_file_path, "wb") as f:
            response.stream_to_file(webm_file_path)

        # Verify the file was created
        if os.path.exists(webm_file_path):
            file_size = os.path.getsize(webm_file_path)
            print(f"Audio file created successfully. Size: {file_size} bytes")
        else:
            print(f"Warning: Audio file was not created at {webm_file_path}")

        # Add a small delay to ensure file is properly written
        time.sleep(1)
        return webm_file_path
    except Exception as e:
        print(f"Error in text_to_speech: {e}")
        # Create an empty audio file as fallback
        fallback_path = f"error_audio_{int(time.time())}.mp3"
        with open(fallback_path, "w") as f:
            f.write("")
        return fallback_path


def autoplay_audio(file_path: str):
    try:
        if not os.path.exists(file_path):
            print(f"Warning: Audio file not found at {file_path}")
            return

        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode("utf-8")
        md = f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
        st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        print(f"Error in autoplay_audio: {e}")
