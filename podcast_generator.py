import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from helpers import text_to_speech, autoplay_audio
import time

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create podcasts directory if it doesn't exist
PODCASTS_DIR = "podcasts"
os.makedirs(PODCASTS_DIR, exist_ok=True)


def generate_podcast_script(report_text: str) -> str:
    """
    Generate a podcast script from an interview evaluation report.

    Args:
        report_text (str): The interview evaluation report text

    Returns:
        str: A podcast-style script based on the evaluation
    """
    # Print debug information
    print(f"Starting podcast script generation. Report text length: {len(report_text)}")

    # Create the system prompt for the podcast script generation
    system_prompt = """
    You are an engaging podcast host who specializes in career development and interview coaching.
    Create an engaging, conversational 8-minute podcast monologue based on an interview evaluation report.
    
    Your podcast should:
    1. Have a friendly, informative tone
    2. Start with a brief introduction of the podcast and episode topic
    3. Highlight the key strengths identified in the report
    4. Tactfully discuss areas for improvement
    5. Provide actionable advice based on the report's recommendations
    6. Include transitions between sections
    7. End with encouraging closing remarks
    
    Format your script to indicate speaker emphasis and pauses where appropriate.
    The podcast should feel like a coach giving personalized feedback in a supportive manner.
    Keep the total length appropriate for an 5-minute podcast (approximately 700-1,000 words).
    """

    # Prepare the messages for the API call
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Here is the interview evaluation report:\n\n{report_text}",
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

    try:
        # Get the evaluation text from session state
        evaluation_text = st.session_state.evaluation
        print(
            f"Retrieved evaluation text from session state. Length: {len(evaluation_text)}"
        )

        # Generate podcast script from the evaluation
        with st.spinner("Generating podcast script..."):
            podcast_script = generate_podcast_script(evaluation_text)
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
