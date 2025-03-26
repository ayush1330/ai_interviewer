import streamlit as st
import os
from helpers import text_to_speech, autoplay_audio, speech_to_text
from generate_answer import conduct_interview, VectorDB
from audio_recorder_streamlit import audio_recorder
from streamlit_float import *
from tempfile import NamedTemporaryFile
from evaluation import evaluate_candidate_performance, display_performance_report
from podcast_generator import create_podcast_from_evaluation

# Create utils directory and session_utils.py
os.makedirs("utils", exist_ok=True)


def main():
    # Initialize float feature
    float_init()

    st.title("AI Interview Assistant 🤖")

    # Initialize session state variables
    if "job_description" not in st.session_state:
        st.session_state.job_description = ""

    # Initialize evaluation state
    if "evaluation" not in st.session_state:
        st.session_state.evaluation = None

    # Initialize interview started flag
    if "interview_started" not in st.session_state:
        st.session_state.interview_started = False

    # Initialize total questions counter
    if "total_questions_asked" not in st.session_state:
        st.session_state.total_questions_asked = 0

    # Track if the last question has been answered
    if "waiting_for_last_answer" not in st.session_state:
        st.session_state.waiting_for_last_answer = False

    # Track if interview is complete and ready for report
    if "interview_complete" not in st.session_state:
        st.session_state.interview_complete = False

    # Check if evaluation is ready to be displayed
    if st.session_state.evaluation is not None:
        display_performance_report()

        # Add Generate Podcast button after the report is displayed
        podcast_col1, podcast_col2 = st.columns([1, 3])

        with podcast_col1:
            st.markdown(
                """
                <style>
                div.stButton > button.podcast-btn {
                    background-color: #4CAF50;
                    color: white;
                    font-weight: bold;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Generate Podcast", key="generate_podcast", type="primary"):
                # Retrieve the interview evaluation text from session state
                evaluation_text = st.session_state.evaluation

                # Generate podcast script from the evaluation
                with st.spinner(
                    "Generating podcast script from your interview evaluation..."
                ):
                    # Call create_podcast_from_evaluation which handles both script and audio generation
                    audio_file = create_podcast_from_evaluation()

                if audio_file and os.path.exists(audio_file):
                    st.success("Podcast generated successfully!")

                    # Play the podcast audio using st.audio
                    st.subheader("Listen to Your Interview Podcast")
                    st.audio(audio_file)
                else:
                    st.error("Failed to generate podcast. Please try again.")

        with podcast_col2:
            st.info("Click to generate a podcast version of your interview highlights.")

        return

    # Only show the upload interface if interview hasn't started
    if not st.session_state.interview_started:
        # Create main layout
        # Resume and Cover Letter in two columns
        col1, col2 = st.columns(2)

        with col1:
            st.header("Resume")
            st.write("Upload your resume (PDF format)")
            resume_file = st.file_uploader("", type=["pdf"], key="resume_uploader")
            if resume_file is not None:
                st.success("Resume uploaded ✓")

        with col2:
            st.header("Cover Letter")
            st.write("Upload your cover letter (PDF format)")
            cover_letter_file = st.file_uploader(
                "", type=["pdf"], key="cover_letter_uploader"
            )
            if cover_letter_file is not None:
                st.success("Cover letter uploaded ✓")

        # Job Description area
        st.header("Job Description")
        job_description = st.text_area(
            "Paste the job description for the position you are applying for...",
            value=st.session_state.job_description,
        )
        st.session_state.job_description = job_description

        # Check if at least one field is provided
        documents_provided = (
            resume_file is not None
            or cover_letter_file is not None
            or job_description.strip()
        )

        if not documents_provided:
            st.warning(
                "Please upload at least your resume, cover letter, or provide a job description to proceed."
            )
        else:
            # Show start interview button with red background like in the screenshot
            start_col1, start_col2 = st.columns([1, 3])
            with start_col1:
                st.markdown(
                    """
                <style>
                div.stButton > button:first-child {
                    background-color: #ff4b4b;
                    color: white;
                    font-weight: bold;
                }
                </style>""",
                    unsafe_allow_html=True,
                )
                if st.button("Start Interview", key="start_interview"):
                    # Save the documents before rerunning
                    if resume_file is not None:
                        with NamedTemporaryFile(
                            delete=False, suffix=".pdf"
                        ) as resume_temp:
                            resume_temp.write(resume_file.getvalue())
                            st.session_state.resume_path = resume_temp.name

                    if cover_letter_file is not None:
                        with NamedTemporaryFile(
                            delete=False, suffix=".pdf"
                        ) as cover_letter_temp:
                            cover_letter_temp.write(cover_letter_file.getvalue())
                            st.session_state.cover_letter_path = cover_letter_temp.name

                    st.session_state.interview_started = True
                    st.rerun()
            with start_col2:
                st.markdown(
                    '<div style="background-color: #192841; padding: 10px; border-radius: 5px;">Click to begin your interview session</div>',
                    unsafe_allow_html=True,
                )

        # Only proceed with interview if the start button has been clicked
        if not st.session_state.interview_started:
            return

    # Interview is started at this point
    # Initialize paths list for VectorDB
    pdf_paths = []

    # Add paths to the list if they exist in session state
    if hasattr(st.session_state, "resume_path") and st.session_state.resume_path:
        pdf_paths.append(st.session_state.resume_path)

    if (
        hasattr(st.session_state, "cover_letter_path")
        and st.session_state.cover_letter_path
    ):
        pdf_paths.append(st.session_state.cover_letter_path)

    # Initialize VectorDB with the paths of the uploaded PDFs
    vector_db = VectorDB(pdf_paths) if pdf_paths else None

    # Show chat interface title when interview has started
    if st.session_state.interview_started:
        st.markdown(
            """
        <style>
        .stChatMessage {
            background-color: #1E1E1E;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )
        st.markdown("### Interview Session")

    # Initialize session state for messages and interview stage if not already set
    if "messages" not in st.session_state:

        initial_greeting = ("Hello and welcome to your interview session!"
                            "I'm delighted to speak with you today.{If pdf_paths exist: “I've had"
                            "the chance to review your documents,”} otherwise: “Based on"
                            "the information you provided,” I'll be asking about your"
                            "experiences, and perspectives. Could you start"
                            "by telling me a bit about your background and the areas you're most passionate about?")
        
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": initial_greeting
            }
        ]
        
        # Generate and play audio for initial greeting
        with st.spinner("Generating audio response..."):
            audio_file = text_to_speech(initial_greeting)
            autoplay_audio(audio_file)
            os.remove(audio_file)

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
    if (
        st.session_state.messages[-1]["role"] != "assistant"
        and st.session_state.total_questions_asked < 3
    ):
        with st.chat_message("assistant"):
            with st.spinner("Thinking🤔..."):
                # Pass the interview stage to the conduct_interview function
                if vector_db:
                    final_response = conduct_interview(
                        st.session_state.messages,
                        vector_db,
                        st.session_state.interview_stage,
                    )
                else:
                    # If no document was uploaded, we'll pass None for vector_db
                    # Make sure to handle this case in conduct_interview function
                    final_response = conduct_interview(
                        st.session_state.messages,
                        None,
                        st.session_state.interview_stage,
                    )

                # Update interview stage - increment questions asked
                st.session_state.interview_stage["questions_asked"] += 1
                st.session_state.total_questions_asked += 1

                # Check if this is the last question (the 3rd one)
                if st.session_state.total_questions_asked == 3:
                    st.session_state.waiting_for_last_answer = True

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

    # Check if all 3 questions have been asked and answered but the thankyou message hasn't been sent
    if (
        st.session_state.total_questions_asked >= 3
        and st.session_state.waiting_for_last_answer
        and st.session_state.messages[-1]["role"] == "user"
        and not st.session_state.interview_complete
    ):

        # Add thank you message
        thank_you_message = "Thank you for completing the interview. Now I'll give you a summary report of your performance."

        with st.chat_message("assistant"):
            with st.spinner("Generating audio response..."):
                audio_file = text_to_speech(thank_you_message)
                autoplay_audio(audio_file)
            st.write(thank_you_message)
            os.remove(audio_file)

        # Add message to session state
        st.session_state.messages.append(
            {"role": "assistant", "content": thank_you_message}
        )

        # Mark interview as complete
        st.session_state.interview_complete = True
        st.session_state.waiting_for_last_answer = False

    # Display Generate Report button if interview is complete
    if st.session_state.interview_complete and st.session_state.evaluation is None:
        report_col1, report_col2 = st.columns([1, 3])

        with report_col1:
            if st.button("Generate Report", type="primary", key="generate_report"):
                with st.spinner("Generating your interview evaluation..."):
                    evaluate_candidate_performance()
                    st.rerun()

        with report_col2:
            st.info("Click to generate your performance report based on the interview.")

    # Float the footer container at the bottom
    footer_container.float("bottom: 0rem;")


if __name__ == "__main__":
    main()
