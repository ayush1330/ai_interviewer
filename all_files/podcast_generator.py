import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from helpers import text_to_speech
import time

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create podcasts directory if it doesn't exist
PODCASTS_DIR = "podcasts"
os.makedirs(PODCASTS_DIR, exist_ok=True)


def generate_podcast_script(interview_messages: list, report_text: str) -> str:
    """
    Generate a podcast script from an interview transcript and evaluation report.

    Args:
        interview_messages (list): The interview conversation messages
        report_text (str): The interview evaluation report text

    Returns:
        str: A podcast-style script based on the evaluation
    """
    # Print debug information
    print(f"Starting podcast script generation. Report text length: {len(report_text)}")
    print(f"Interview messages count: {len(interview_messages)}")

    # Format interview transcript
    interview_transcript = ""
    for msg in interview_messages:
        role = "Interviewer" if msg["role"] == "assistant" else "Candidate"
        interview_transcript += f"{role}: {msg['content']}\n\n"

    # Create the system prompt for the podcast script generation
    system_prompt = """
    You are a friendly, experienced host and coach specializing in interview coaching. Based on the interview transcript and evaluation report, create A cohesive podcast script (300-500 words) that includes a friendly introduction, specific feedback from the interview, actionable advice, balanced strengths and improvement points, smooth transitions between sections, and an encouraging conclusion—all delivered in a supportive, coach-like manner:
    
Begin with a brief introduction to the podcast and the episode's topic.
Quote specific moments from the interview where the candidate could have improved. For example, "When you mentioned, I faced challenges while building the project, you could have elaborated on which specific challenges and how you overcame them."
Identify and emphasize strength from the evaluation report. Explain how this strength contributes positively to the candidate's overall performance.
Clearly outline areas where the candidate can improve it's mistakes by referencing specific points from the transcript.
Use transitions to smoothly move from discussing strengths to areas for improvement. For instance, "While your explanation about project specifics was strong, there's room to improve by adding more measurable results."
Offer concrete suggestions on how to refine their answers, such as "Include more details about your results," "Showcase teamwork by describing your collaboration process," or "Clarify your role with concrete examples."
Use clear, conversational transition phrases to guide listeners from one topic to the next, ensuring the monologue flows naturally.
Conclude with a concise, uplifting summary that motivates the candidate to keep practicing.
Reaffirm the candidate's potential and leave the listener with an encouraging message, using brief pauses to create a dynamic podcast feel.
    """

    # Prepare the messages for the API call
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Here is the interview transcript:\n\n{interview_transcript}\n\nHere is the interview evaluation report:\n\n{report_text}",
        },
    ]

    try:
        # Make the API call
        print("Calling OpenAI API to generate podcast script...")
        response = client.chat.completions.create(
            model="gpt-4o",  # Using the same model as in evaluation.py
            messages=messages,
            max_tokens=2000,
            temperature=0.7,
        )

        # Return the generated podcast script
        podcast_script = response.choices[0].message.content

        print(f"Podcast script generated successfully. Length: {len(podcast_script)}")
        # Print the first 100 characters for debugging
        print(f"Script preview: {podcast_script[:100]}...")

        return podcast_script

    except Exception as e:
        print(f"Error generating podcast script: {e}")
        # Return a fallback message in case of an error
        return "We couldn't generate your podcast script at this time. Please try again later."


def generate_audio(script_text: str) -> str:
    """
    Convert text to speech using the existing text_to_speech function.

    Args:
        script_text (str): The text to convert to speech

    Returns:
        str: The file path to the generated MP3 audio file
    """
    try:
        print(f"Converting script to audio. Script length: {len(script_text)}")
        # Call the text_to_speech function from helpers.py
        temp_audio_file_path = text_to_speech(script_text)
        print(f"Audio generated successfully in temp location: {temp_audio_file_path}")

        # Create a permanent file in the podcasts directory
        timestamp = int(time.time())
        podcast_filename = f"interview_podcast_{timestamp}.mp3"
        podcast_filepath = os.path.join(PODCASTS_DIR, podcast_filename)

        # Copy the temporary file to the podcasts directory
        import shutil

        shutil.copy2(temp_audio_file_path, podcast_filepath)
        print(f"Audio file copied to permanent location: {podcast_filepath}")

        # Clean up temporary file
        try:
            os.remove(temp_audio_file_path)
            print(f"Temporary audio file removed: {temp_audio_file_path}")
        except:
            print(f"Note: Could not remove temporary file: {temp_audio_file_path}")

        # Ensure the file exists
        if os.path.exists(podcast_filepath):
            file_size = os.path.getsize(podcast_filepath)
            print(f"Audio file exists in podcasts directory. Size: {file_size} bytes")

            # Add a small delay to ensure file is properly written
            time.sleep(1)
            return podcast_filepath
        else:
            print(f"Warning: Audio file not found at {podcast_filepath}")
            return None
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None


def create_podcast_from_evaluation():
    """
    Creates a podcast from the evaluation stored in the session state.
    Generates both the script and audio version of the podcast.

    Returns:
        str: Path to the generated audio file, or None if generation failed
    """
    # Check if evaluation exists in session state
    if not st.session_state.evaluation:
        st.warning(
            "No evaluation available. Please complete the interview and generate a report first."
        )
        return None

    # Check if interview messages exist
    if "messages" not in st.session_state or not st.session_state.messages:
        st.warning(
            "No interview transcript available. Please complete an interview first."
        )
        return None

    try:
        # Get the evaluation text and interview messages from session state
        evaluation_text = st.session_state.evaluation
        interview_messages = st.session_state.messages
        print(
            f"Retrieved evaluation text from session state. Length: {len(evaluation_text)}"
        )
        print(f"Retrieved interview messages. Count: {len(interview_messages)}")

        # Generate podcast script from the evaluation and interview transcript
        with st.spinner("Generating podcast script..."):
            podcast_script = generate_podcast_script(
                interview_messages, evaluation_text
            )
            if not podcast_script or podcast_script.startswith("We couldn't generate"):
                st.error("Failed to generate podcast script. Please try again.")
                return None

            # Store the podcast script in session state for later use
            st.session_state.podcast_script = podcast_script
            print("Podcast script stored in session state")

        # Generate audio from the podcast script using the new function
        with st.spinner("Converting podcast script to audio..."):
            audio_file = generate_audio(podcast_script)

            if not audio_file:
                st.error("Failed to generate audio. Please try again.")
                return None

            # Store the audio file path in session state
            st.session_state.podcast_audio_path = audio_file
            print(f"Audio file path stored in session state: {audio_file}")

            return audio_file

    except Exception as e:
        print(f"Error creating podcast: {e}")
        st.error(f"Error creating podcast: {str(e)}")
        return None
