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

    # Add custom CSS for professional styling, including minimal mic styling
    st.markdown(
        """
    <style>
    /* Main background with gradient */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4ecfb 100%);
    }
    
    /* Special styling for the Actionable Tips box */
    .actionable-tips-box {
        background-color: #f0f0f0;
        color: #000000;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #4776E6;
        margin-bottom: 20px;
        font-family: 'Arial', sans-serif;
    }
    
    /* Main title styling with enhanced appearance */
    .main-title {
        color: #283E4A;
        font-size: 48px;
        font-weight: 800;
        margin-bottom: 5px;
        text-align: center;
        padding: 10px 0 0 0;
        font-family: 'Arial', sans-serif;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        background: linear-gradient(90deg, #283E4A, #4776E6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
    }
    
    /* Subtitle styling */
    .subtitle {
        color: #4A4A4A;
        font-size: 18px;
        margin-bottom: 30px;
        text-align: center;
        font-family: 'Arial', sans-serif;
        font-weight: 400;
    }
    
    /* Section headers styling with improved visual interest */
    .section-header {
        color: #283E4A;
        font-size: 22px;
        font-weight: 700;
        margin: 12px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #4776E6;
        font-family: 'Arial', sans-serif;
        position: relative;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .section-header:after {
        content: "";
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 100%;
        height: 1px;
        background: linear-gradient(to right, transparent, rgba(71, 118, 230, 0.4), transparent);
    }
    
    /* Section container styling for better visual separation */
    .section-container {
        background-color: #f0f0f0;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border-top: 5px solid #4776E6;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        color: #000000;
    }
    
    .section-container:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
    }
    
    /* File uploader styling */
    .stFileUploader > div > button {
        background-color: #4776E6 !important;
        color: white !important;
        font-family: 'Arial', sans-serif !important;
        font-weight: 600 !important;
        padding: 4px 15px !important;
        border-radius: 30px !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }
    
    .stFileUploader > div > button:hover {
        background-color: #3A5FBB !important;
        box-shadow: 0 4px 10px rgba(71, 118, 230, 0.3) !important;
        transform: translateY(-2px);
    }
    
    /* Text area styling */
    .stTextArea textarea {
        background-color: white;
        color: #343A40;
        border: 1px solid #CED4DA;
        border-radius: 8px;
        font-family: 'Arial', sans-serif;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: #4776E6 !important;
        box-shadow: 0 0 0 3px rgba(71, 118, 230, 0.2) !important;
    }
    
    /* Job description styling */
    .job-description-section {
        color: #283E4A !important;
        font-size: 22px;
        font-weight: 700;
        margin: 12px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #4776E6 !important;
        font-family: 'Arial', sans-serif;
        position: relative;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .job-description-section:after {
        content: "";
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 100%;
        height: 1px;
        background: linear-gradient(to right, transparent, rgba(71, 118, 230, 0.4), transparent) !important;
    }
    
    /* Custom styles for Cover Letter specifically */
    .cover-letter-header {
        white-space: nowrap;
        font-size: 22px;
        font-weight: 700;
    }
    
    /* Card icon styling */
    .header-icon {
        display: inline-block;
        margin-right: 5px;
    }
    
    /* Override all textarea stylings */
    textarea, .stTextArea textarea, [data-testid="stTextArea"] textarea {
        background-color: white !important;
        color: #343A40 !important;
        border: 1px solid #CED4DA !important;
        border-radius: 8px;
        font-family: 'Arial', sans-serif;
        padding: 12px !important;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Specific selector for job description textarea */
    [data-testid="stTextArea"][key="job_description_textarea"] textarea {
        background-color: white !important;
        color: #343A40 !important;
        border: 1px solid #CED4DA !important;
    }
    
    /* Streamlit default button override */
    div.stButton > button:first-child {
        background-color: #4776E6;
        color: white;
        border: none;
        font-weight: 600;
        font-family: 'Arial', sans-serif;
        transition: all 0.3s ease;
        border-radius: 30px;
        padding: 5px 20px;
    }
    
    div.stButton > button:hover {
        background-color: #3A5FBB;
        color: white;
        border: none;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Success message styling */
    .element-container div[data-testid="stText"] {
        background-color: #edfaf1 !important;
        color: #1e7f4c !important;
        padding: 8px 15px !important;
        border-radius: 6px !important;
        border-left: 4px solid #2ec973 !important;
        font-weight: 500 !important;
        margin: 10px 0 !important;
    }
    
    /* Animated icon pulse effect */
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    .floating-icon {
        animation: float 3s ease-in-out infinite;
        filter: drop-shadow(0 5px 15px rgba(0,0,0,0.1));
    }
    
    /* Warning message styling */
    .stAlert {
        border-radius: 8px !important;
        border-left-width: 4px !important;
    }
    
    /* Chat message styling */
    [data-testid="stChatMessage"] {
        background-color: white !important;
        border-radius: 15px !important;
        padding: 15px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05) !important;
        margin-bottom: 15px !important;
        border-left: 3px solid #4776E6 !important;
    }
    
    /* Custom styling for audio recorder container */
    .audio-recorder {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Hide tooltips and instruction messages */
    [data-testid="InputInstructions"] {display: none !important;}
    
    /* Enhanced start button styling */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1E3A5F, #2C4D7C) !important;
        color: white !important;
        font-size: 22px !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 15px 30px !important;
        width: 100% !important;
        transition: all 0.4s ease !important;
        box-shadow: 0 10px 20px rgba(30, 58, 95, 0.5) !important;
        letter-spacing: 1px !important;
        position: relative !important;
        overflow: hidden !important;
        z-index: 1 !important;
    }
    
    /* Hover effect with light sweep */
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-7px) !important;
        box-shadow: 0 15px 30px rgba(30, 58, 95, 0.6) !important;
        background: linear-gradient(135deg, #254470, #3A5E8E) !important;
    }
    
    /* Active state */
    div.stButton > button[kind="primary"]:active {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 15px rgba(30, 58, 95, 0.5) !important;
    }
    
    /* Minimal CSS for mic icon styling */
    .audio-recorder svg {
        font-size: 1.5rem !important;
        color: #4776E6 !important;
        margin-left: 0 !important;
    }
    .audio-recorder svg[style*="color"] {
        color: #FF3B30 !important;
    }
    
    /* Info box styling */
    .info-box {
        background-color: #e6e6e6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 3px solid #4776E6;
        font-family: 'Arial', sans-serif;
        color: #000000;
    }
    
    /* Make audio player wider */
    .stAudio {
        width: 100% !important;
    }
    .stAudio > div {
        width: 100% !important;
        max-width: 100% !important;
    }
    .stAudio audio {
        width: 100% !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Enhanced title with animated icon
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 10px;">
            <span style="font-size: 70px;" class="floating-icon">👨‍💼</span>
        </div>
        <h1 class="main-title">Interview Assistant</h1>
        <p class="subtitle">Prepare for your next job interview with AI-powered practice</p>
        """,
        unsafe_allow_html=True,
    )

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

        # Add Generate Podcast button in a centered column
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Generate Podcast", key="generate_podcast", type="primary"):
                # Retrieve the interview evaluation text from session_state
                evaluation_text = st.session_state.evaluation

                # Generate podcast script from the evaluation
                with st.spinner(
                    "Generating podcast script from your interview evaluation..."
                ):
                    # Call create_podcast_from_evaluation which handles both script and audio generation
                    audio_file = create_podcast_from_evaluation()

                if audio_file and os.path.exists(audio_file):
                    st.success("Podcast generated successfully!")

                    # Play the podcast audio using st.audio in full width
                    st.markdown(
                        '<h3 class="section-header">Listen to Your Interview Podcast</h3>',
                        unsafe_allow_html=True,
                    )
                    st.audio(audio_file)
                else:
                    st.error("Failed to generate podcast. Please try again.")

        return

    # Only show the upload interface if interview hasn't started
    if not st.session_state.interview_started:
        # Create main layout
        # Resume and Cover Letter in two columns
        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown(
                """
                <div class="section-container">
                    <h2 class="section-header"><span class="header-icon">📄</span> Resume</h2>
                    <p style='font-size: 14px; margin-top: 0px; color: #555;'>
                        Upload your resume to help tailor interview questions to your experience
                    </p>
                """,
                unsafe_allow_html=True,
            )
            resume_file = st.file_uploader("", type=["pdf"], key="resume_uploader")
            if resume_file is not None:
                st.success("Resume uploaded successfully ✓")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown(
                """
                <div class="section-container">
                    <h2 class="section-header cover-letter-header"><span class="header-icon">📝</span> Cover Letter</h2>
                    <p style='font-size: 14px; margin-top: 0px; color: #555;'>
                        Upload your cover letter to receive more personalized feedback
                    </p>
                """,
                unsafe_allow_html=True,
            )
            cover_letter_file = st.file_uploader(
                "", type=["pdf"], key="cover_letter_uploader"
            )
            if cover_letter_file is not None:
                st.success("Cover letter uploaded successfully ✓")
            st.markdown("</div>", unsafe_allow_html=True)

        # Job Description area with enhanced styling
        st.markdown(
            """
            <div class="section-container">
                <h2 class="job-description-section"><span class="header-icon">💼</span> Job Description</h2>
                <p style='font-size: 14px; margin-top: 0px; color: #555;'>
                    Paste the job description to help tailor the interview questions to the role
                </p>
            """,
            unsafe_allow_html=True,
        )

        # Add a custom placeholder style for the job description
        st.markdown(
            """
            <style>
            [data-testid="stTextArea"] .stTextArea p {
                font-size: 14px !important;
                color: #555 !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        job_description = st.text_area(
            "Enter job description...",
            value=st.session_state.job_description,
            key="job_description_textarea",
            height=150,
        )
        st.session_state.job_description = job_description
        st.markdown("</div>", unsafe_allow_html=True)

        # Check if at least one field is provided
        documents_provided = (
            resume_file is not None
            or cover_letter_file is not None
            or job_description.strip()
        )

        if not documents_provided:
            st.warning(
                "📋 Please upload at least your resume, cover letter, or provide a job description to begin."
            )
        else:
            # Show start interview button with enhanced styling and centered layout
            st.markdown("<br>", unsafe_allow_html=True)
            start_col1, start_col2, start_col3 = st.columns([1, 2, 1])
            with start_col2:
                st.markdown(
                    """
                    <style>
                    /* Enhanced start button styling */
                    div.stButton > button[kind="primary"] {
                        background: linear-gradient(135deg, #1E3A5F, #2C4D7C) !important;
                        color: white !important;
                        font-size: 22px !important;
                        font-weight: bold !important;
                        border: none !important;
                        border-radius: 50px !important;
                        padding: 15px 30px !important;
                        width: 100% !important;
                        transition: all 0.4s ease !important;
                        box-shadow: 0 10px 20px rgba(30, 58, 95, 0.5) !important;
                        letter-spacing: 1px !important;
                        position: relative !important;
                        overflow: hidden !important;
                        z-index: 1 !important;
                    }
                    
                    /* Hover effect with light sweep */
                    div.stButton > button[kind="primary"]:hover {
                        transform: translateY(-7px) !important;
                        box-shadow: 0 15px 30px rgba(30, 58, 95, 0.6) !important;
                        background: linear-gradient(135deg, #254470, #3A5E8E) !important;
                    }
                    
                    /* Active state */
                    div.stButton > button[kind="primary"]:active {
                        transform: translateY(-3px) !important;
                        box-shadow: 0 8px 15px rgba(30, 58, 95, 0.5) !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(
                    "🚀 Start Your Interview", key="start_interview", type="primary"
                ):
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
            '<h3 class="section-header">Interview Session</h3>', unsafe_allow_html=True
        )

    # Initialize session state for messages and interview stage if not already set
    if "messages" not in st.session_state:
        initial_greeting = (
            "Hello, and welcome to your interview session! "
            "I'll be your interviewer today, focusing on both the technical "
            "and behavioral aspects of your background. "
            f"{'I have reviewed your documents' if pdf_paths else 'Based on your information'}, "
            "I'll be asking questions about your "
            "experiences, achievements, and perspectives. "
            "I'll ask you 3 questions, and then provide an evaluation. "
            "Could you start by telling me about your background and "
            "which areas you're most passionate about?"
        )

        st.session_state.messages = [{"role": "assistant", "content": initial_greeting}]

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

    # ---------------------------------------------------------
    # Updated Footer: Simple mic layout with one "Click to record" label
    footer_container = st.container()
    with footer_container:
        # Create two columns: one for the label+mic, and an empty one for spacing if needed
        mic_col1, mic_col2 = st.columns([1, 4])
        with mic_col1:
            st.markdown(
                """
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
                    <span style="
                        color: #4776E6;
                        font-weight: 600;
                        font-size: 16px;
                        font-family: 'Montserrat', 'Roboto', sans-serif;
                        letter-spacing: 0.3px;">
                        Click to record
                    </span>
                    <div id="my_audio_recorder"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Pass text="" to remove the default "Click to record" label from the library
            audio_bytes = audio_recorder(
                pause_threshold=2.0,
                icon_size="2x",
                recording_color="#FF3B30",
                neutral_color="#4776E6",
                text="",  # <-- This ensures no duplicate "Click to record" text
                key="my_audio_recorder",
            )
            # We do NOT show "Audio has been recorded." anymore
    # ---------------------------------------------------------

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
                if vector_db:
                    final_response = conduct_interview(
                        st.session_state.messages,
                        vector_db,
                        st.session_state.interview_stage,
                    )
                else:
                    final_response = conduct_interview(
                        st.session_state.messages,
                        None,
                        st.session_state.interview_stage,
                    )

                st.session_state.interview_stage["questions_asked"] += 1
                st.session_state.total_questions_asked += 1

                if st.session_state.total_questions_asked == 3:
                    st.session_state.waiting_for_last_answer = True

                if st.session_state.interview_stage["questions_asked"] >= 2:
                    stages = st.session_state.interview_stage["stages"]
                    current_index = stages.index(
                        st.session_state.interview_stage["current"]
                    )
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
        thank_you_message = "Thank you for completing the interview. Now I'll give you a summary report of your performance."

        with st.chat_message("assistant"):
            with st.spinner("Generating audio response..."):
                audio_file = text_to_speech(thank_you_message)
                autoplay_audio(audio_file)
            st.write(thank_you_message)
            os.remove(audio_file)

        st.session_state.messages.append(
            {"role": "assistant", "content": thank_you_message}
        )

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

    footer_container.float("bottom: 0rem;")


if __name__ == "__main__":
    main()
