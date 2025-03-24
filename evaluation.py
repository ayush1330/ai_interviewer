import os
import re
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from utils.session_utils import reset_interview

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def evaluate_candidate_performance():
    """
    Generate a comprehensive evaluation of the student's interview performance
    using OpenAI's API and store it in the session state
    """
    # Get messages from session state
    messages = st.session_state.messages

    # Extract job description if available
    job_description = st.session_state.job_description or "AI/ML position"

    # Prepare the system prompt for evaluation - simplified format for better parsing
    system_prompt = f"""
    You are an expert interview coach for students. I'd like you to evaluate a student's interview performance.
    The role they practiced interviewing for is: {job_description}
    
    Please evaluate the student based on the conversation transcript I'll provide.
    Your evaluation should include:
    
    1. SUMMARY: A brief 2-3 sentence overview of the student's performance
    
    2. STRENGTHS: List exactly 3 clear strengths the student demonstrated
    
    3. AREAS_TO_IMPROVE: List exactly 3 clear areas for improvement
    
    4. ACTIONABLE_TIPS: A brief paragraph with specific, actionable tips for future interviews
    
    5. SCORES: Rate on a scale of 1-10 for each category:
       - Technical: [1-10]
       - Communication: [1-10]
       - Problem Solving: [1-10]
       - Professional Presence: [1-10]
       - Overall: [1-10]
    
    Format each section with the section name in capital letters followed by a colon, like "SUMMARY:" followed by the content.
    Keep your responses concise, constructive and focused on helping the student improve for future interviews.
    
    Important: Make sure to strictly follow the format with section headers like SUMMARY:, STRENGTHS:, etc.
    """

    # Prepare the messages for the API call
    api_messages = [{"role": "system", "content": system_prompt}]

    # Add all the interview messages
    for msg in messages:
        # Convert the roles to match what the API expects
        role = msg["role"]
        # Skip system messages since we already added our custom system message
        if role == "system":
            continue
        api_messages.append({"role": role, "content": msg["content"]})
    
    try:
        # Make the API call
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=api_messages,
            max_tokens=1500,
            temperature=0.7,
        )

        # Store the evaluation in the session state
        evaluation_text = response.choices[0].message.content
        
        # Check if the evaluation has proper sections
        if not any(section in evaluation_text for section in ["SUMMARY:", "STRENGTHS:", "SCORES:"]):
            st.warning("API response didn't match expected format. Using fallback evaluation.")
            evaluation_text = create_fallback_evaluation(messages)
            
        st.session_state.evaluation = evaluation_text
        
        # Log the evaluation text for debugging
        print("Evaluation generated:", st.session_state.evaluation[:100] + "...")
        
    except Exception as e:
        st.error(f"Error generating evaluation: {e}")
        st.session_state.evaluation = create_fallback_evaluation(messages)


def create_fallback_evaluation(messages):
    """Create a fallback evaluation when the API call fails or returns improper format"""
    return """SUMMARY: The student demonstrated a good understanding of the interview process and provided relevant responses to the questions asked. There were some areas that could be improved, but overall this was a solid performance.

STRENGTHS:
1. Clear communication with well-structured responses
2. Good use of specific examples to illustrate points
3. Maintained professional demeanor throughout the interview

AREAS_TO_IMPROVE:
1. Could provide more detailed technical explanations
2. Sometimes responses were too general
3. Could demonstrate more knowledge of the specific industry

ACTIONABLE_TIPS: Before your next interview, research the company more thoroughly and prepare specific examples of your work that directly relate to the position. Practice answering technical questions with more precision and depth. Consider recording yourself in mock interviews to identify areas where you can improve your delivery.

SCORES:
- Technical: 7
- Communication: 8
- Problem Solving: 7
- Professional Presence: 8
- Overall: 7
"""


def display_performance_report():
    """
    Display the performance evaluation report with visualizations
    """
    # Check if evaluation exists
    if not st.session_state.evaluation:
        st.warning("No evaluation available. Please complete the interview first.")
        return

    # Apply custom CSS for better styling
    st.markdown("""
    <style>
    .report-header {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
        text-align: center;
    }
    .section-header {
        border-left: 4px solid #FFC107;
        padding-left: 10px;
        margin-top: 30px;
        margin-bottom: 20px;
    }
    .card-container {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .score-card {
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
    }
    .score-card:hover {
        transform: translateY(-5px);
    }
    .score-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 10px 0;
    }
    .score-label {
        font-size: 1.2rem;
        font-weight: 500;
    }
    .info-box {
        background-color: #192841;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .point-list {
        list-style-type: none;
        padding-left: 0;
    }
    .point-list li {
        position: relative;
        padding-left: 30px;
        margin-bottom: 10px;
        font-size: 16px;
    }
    .point-list li:before {
        content: "✓";
        position: absolute;
        left: 0;
        color: #4CAF50;
        font-weight: bold;
    }
    .weak-list li:before {
        content: "!";
        color: #FFC107;
    }
    .tips-box {
        background-color: #143624;
        border-radius: 10px;
        padding: 20px;
        border-left: 4px solid #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

    # Display the title with enhanced styling
    st.markdown('<div class="report-header"><h1>Interview Performance Report 📊</h1></div>', unsafe_allow_html=True)
    
    # Extract sections from the evaluation using more reliable patterns
    evaluation_text = st.session_state.evaluation
    
    if not evaluation_text or len(evaluation_text) < 10:
        st.error("The evaluation text is empty or too short. There might be an issue with the API response.")
        return

    # Use simpler, more lenient pattern matching
    def extract_section_simple(text, keywords):
        for keyword in keywords:
            pattern = rf"{keyword}:?\s*(.*?)(?:(?:[A-Z]{{4,}}:)|$)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                if content:
                    return content
        return None
        
    # Parse evaluation text with backup keywords
    summary = extract_section_simple(evaluation_text, ["SUMMARY", "OVERVIEW", "PERFORMANCE"])
    strengths = extract_section_simple(evaluation_text, ["STRENGTHS", "STRONG POINTS", "POSITIVES"])
    areas_to_improve = extract_section_simple(evaluation_text, ["AREAS_TO_IMPROVE", "WEAKNESSES", "IMPROVEMENT AREAS", "AREAS FOR IMPROVEMENT"])
    actionable_tips = extract_section_simple(evaluation_text, ["ACTIONABLE_TIPS", "TIPS", "ADVICE", "IMPROVEMENT", "RECOMMENDATIONS"])
    scores_section = extract_section_simple(evaluation_text, ["SCORES", "RATINGS", "EVALUATION"])
    
    # Extract scores using simple patterns
    scores = {}
    if scores_section:
        score_patterns = {
            "Technical": [r"Technical:?\s*(\d+)", r"Technical Knowledge:?\s*(\d+)", r"Technical Skills:?\s*(\d+)"],
            "Communication": [r"Communication:?\s*(\d+)", r"Communication Skills:?\s*(\d+)"],
            "Problem Solving": [r"Problem\s*Solving:?\s*(\d+)", r"Problem-Solving:?\s*(\d+)"],
            "Professional Presence": [r"Professional\s*Presence:?\s*(\d+)", r"Cultural\s*Fit:?\s*(\d+)", r"Professionalism:?\s*(\d+)"],
            "Overall": [r"Overall:?\s*(\d+)", r"Overall Score:?\s*(\d+)", r"Overall Rating:?\s*(\d+)"]
        }
        
        for category, patterns in score_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, scores_section, re.IGNORECASE)
                if match:
                    try:
                        score = int(match.group(1))
                        if 1 <= score <= 10:  # Validate score is in expected range
                            scores[category] = score
                            break
                    except (ValueError, IndexError):
                        pass
                        
    # If we can't extract scores from a section, try to find them in the entire text
    if not scores:
        for category, patterns in score_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, evaluation_text, re.IGNORECASE)
                if match:
                    try:
                        score = int(match.group(1))
                        if 1 <= score <= 10:
                            scores[category] = score
                            break
                    except (ValueError, IndexError):
                        pass
    
    # If still no scores, provide defaults for visual demonstration
    if not scores and not summary and not strengths and not areas_to_improve:
        st.warning("Could not extract any meaningful evaluation data. Using example data for demonstration.")
        summary = "This is an example summary since we couldn't extract data from the evaluation."
        strengths = "1. Example strength 1\n2. Example strength 2\n3. Example strength 3"
        areas_to_improve = "1. Example area to improve 1\n2. Example area to improve 2\n3. Example area to improve 3"
        actionable_tips = "Here are some example actionable tips for your future interviews."
        scores = {
            "Technical": 7,
            "Communication": 8,
            "Problem Solving": 6,
            "Professional Presence": 7,
            "Overall": 7
        }
    
    # Display Performance Summary in an info box
    st.markdown('<h2 class="section-header">Performance Summary</h2>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-box">{summary if summary else "No summary available."}</div>', unsafe_allow_html=True)
    
    # Display score cards in a row with enhanced styling
    st.markdown('<h2 class="section-header">Performance Scores</h2>', unsafe_allow_html=True)
    
    # Only create the score cards if we have scores
    if scores:
        # Define colors for different scores
        def get_score_color(score):
            if score >= 8:
                return "linear-gradient(135deg, #4CAF50, #2E7D32)"  # Green gradient
            elif score >= 6:
                return "linear-gradient(135deg, #FFC107, #FF8F00)"  # Yellow gradient
            else:
                return "linear-gradient(135deg, #F44336, #B71C1C)"  # Red gradient
        
        # Get score emojis
        def get_score_emoji(score):
            if score >= 8:
                return "🌟"
            elif score >= 6:
                return "👍"
            else:
                return "💪"
                
        # Create a container for all score cards
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        
        # Create columns for the score cards
        cols = st.columns(len(scores))
        
        # Display each score in a card with enhanced styling
        for i, (category, score) in enumerate(scores.items()):
            with cols[i]:
                st.markdown(
                    f"""
                    <div class="score-card" style="background: {get_score_color(score)}">
                        <div class="score-label">{category}</div>
                        <div class="score-value">{score}/10 {get_score_emoji(score)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        # Close the container
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No scores available.")
    
    # Create two columns for strengths and weaknesses with enhanced styling
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    # Display strengths
    with col1:
        st.markdown('<h2 class="section-header">Strengths</h2>', unsafe_allow_html=True)
        if strengths:
            # Convert to bullet points if not already formatted
            strength_points = re.split(r'(?:\d+\.\s*|\n+)', strengths)
            strength_points = [s.strip() for s in strength_points if s.strip()]
            
            # Format as an HTML list with custom styling
            points_html = '<ul class="point-list">'
            for point in strength_points:
                if point:  # Only add non-empty points
                    points_html += f'<li>{point}</li>'
            points_html += '</ul>'
            
            st.markdown(points_html, unsafe_allow_html=True)
        else:
            st.info("No strengths data available.")
    
    # Display weaknesses
    with col2:
        st.markdown('<h2 class="section-header">Weaknesses</h2>', unsafe_allow_html=True)
        if areas_to_improve:
            # Convert to bullet points if not already formatted
            weakness_points = re.split(r'(?:\d+\.\s*|\n+)', areas_to_improve)
            weakness_points = [w.strip() for w in weakness_points if w.strip()]
            
            # Format as an HTML list with custom styling
            points_html = '<ul class="point-list weak-list">'
            for point in weakness_points:
                if point:  # Only add non-empty points
                    points_html += f'<li>{point}</li>'
            points_html += '</ul>'
            
            st.markdown(points_html, unsafe_allow_html=True)
        else:
            st.info("No weakness data available.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display improvement paragraph with enhanced styling
    st.markdown('<h2 class="section-header">Actionable Tips for Future Interviews</h2>', unsafe_allow_html=True)
    if actionable_tips:
        st.markdown(f'<div class="tips-box">{actionable_tips}</div>', unsafe_allow_html=True)
    else:
        st.info("No actionable tips available.")
    
    # End of report


def extract_section(text, section_name):
    """Extract a section from the evaluation text using a more reliable pattern"""
    pattern = rf"{section_name}:?\s*(.*?)(?:(?:[A-Z]{{5,}})|$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None
