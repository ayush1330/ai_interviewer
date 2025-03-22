import streamlit as st
import os
from helpers import text_to_speech, autoplay_audio, speech_to_text
from generate_answer import conduct_interview, VectorDB
from audio_recorder_streamlit import audio_recorder
from streamlit_float import *
from tempfile import NamedTemporaryFile


def main():
    # Initialize float feature
    float_init()

    st.title("AI Interview Assistant 🤖")

    # Prompt user to upload resume and cover letter PDFs
    st.sidebar.header("Upload Your Documents")
    resume_file = st.sidebar.file_uploader("Upload your resume (PDF)", type=["pdf"])
    cover_letter_file = st.sidebar.file_uploader(
        "Upload your cover letter (PDF)", type=["pdf"]
    )

    # Ensure both files are uploaded before proceeding
    if resume_file is None or cover_letter_file is None:
        st.sidebar.warning(
            "Please upload both your resume and cover letter to proceed."
        )
        st.stop()

    # Save uploaded files temporarily
    with NamedTemporaryFile(delete=False, suffix=".pdf") as resume_temp:
        resume_temp.write(resume_file.getvalue())
        resume_path = resume_temp.name

    with NamedTemporaryFile(delete=False, suffix=".pdf") as cover_letter_temp:
        cover_letter_temp.write(cover_letter_file.getvalue())
        cover_letter_path = cover_letter_temp.name

    # Initialize VectorDB with the paths of the uploaded PDFs
    vector_db = VectorDB([resume_path, cover_letter_path])

    # Initialize session state for messages and interview stage if not already set
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Welcome to your AI interview session. I'll be conducting a structured technical and behavioral interview for an AI-related position. I've reviewed your resume and cover letter, and I'll be asking questions based on your experience. Let's begin: Tell me about your background in AI and what specific areas you specialize in.",
            }
        ]

    if "interview_stage" not in st.session_state:
        st.session_state.interview_stage = {
            "current": "introduction",
            "stages": [
                "introduction",
                "technical",
                "behavioral",
                "experience",
                "closing",
            ],
            "questions_asked": 0,
        }

    # Create footer container for the microphone
    footer_container = st.container()
    with footer_container:
        audio_bytes = audio_recorder()

    # Display all conversation messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Process audio input if available
    if audio_bytes:
        with st.spinner("Transcribing..."):
            webm_file_path = "temp_audio.mp3"
            with open(webm_file_path, "wb") as f:
                f.write(audio_bytes)
            transcript = speech_to_text(webm_file_path)
            if transcript:
                st.session_state.messages.append(
                    {"role": "user", "content": transcript}
                )
                with st.chat_message("user"):
                    st.write(transcript)
                os.remove(webm_file_path)

    # If the last message is not from the assistant, generate a response
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking🤔..."):
                # Pass the interview stage to the conduct_interview function
                final_response = conduct_interview(
                    st.session_state.messages,
                    vector_db,
                    st.session_state.interview_stage,
                )

                # Update interview stage - increment questions asked
                st.session_state.interview_stage["questions_asked"] += 1

                # Progress to next stage based on number of questions
                if st.session_state.interview_stage["questions_asked"] >= 2:
                    stages = st.session_state.interview_stage["stages"]
                    current_index = stages.index(
                        st.session_state.interview_stage["current"]
                    )

                    # Move to next stage if not already at the last stage
                    if current_index < len(stages) - 1:
                        st.session_state.interview_stage["current"] = stages[
                            current_index + 1
                        ]
                        st.session_state.interview_stage["questions_asked"] = 0

            with st.spinner("Generating audio response..."):
                audio_file = text_to_speech(final_response)
                autoplay_audio(audio_file)
            st.write(final_response)
            st.session_state.messages.append(
                {"role": "assistant", "content": final_response}
            )
            os.remove(audio_file)

    # Float the footer container at the bottom
    footer_container.float("bottom: 0rem;")


if __name__ == "__main__":
    main()
