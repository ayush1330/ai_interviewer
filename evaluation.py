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
   You are an unbiased, professional evaluator. Your task is to assess the student's interview performance.
Use the interview script to inform your evaluation, focusing on the following aspects:

1.Reference specific statements or examples from the conversation to support your observations.
2.Align your feedback with the role's requirements (technical, behavioral, etc.).
3.Highlight both strengths and areas needing improvement.
4.Offer actionable suggestions for future growth.
5.Highlight what mistakes the candidate made and how it can be improved.
6.Fact check if the answers given were factually correct or not. 
Your response must follow this exact format with clearly labeled headings:
SUMMARY:
Provide a brief 2-3 sentence overview of the student's overall performance.
STRENGTHS:
List clear strengths the student demonstrated, referencing specific moments if relevant.
AREAS_TO_IMPROVE:
List focused areas where the student could improve, again referencing specific moments when possible.
ACTIONABLE_TIPS:
Provide a short paragraph of specific, concrete strategies for improving these areas. Consider how the student can apply these strategies in future interviews.
SCORES:
Assign a numerical rating (1-10) for each category below, based on how well the student's performance aligns with the role's requirements:
Technical: [1-10]
Communication: [1-10]
Problem Solving: [1-10]
Overall: [1-10]
Ensure your feedback is concise, unbiased, and fair, offering the student practical guidance for improvement while acknowledging their demonstrated strengths.
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
        if not any(
            section in evaluation_text
            for section in ["SUMMARY:", "STRENGTHS:", "SCORES:"]
        ):
            st.warning(
                "API response didn't match expected format. Using fallback evaluation."
            )
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

    # Extract sections from the evaluation
    evaluation_text = st.session_state.evaluation

    # Parse evaluation sections
    def extract_section(text, keywords):
        for keyword in keywords:
            pattern = rf"{keyword}:?\s*(.*?)(?:(?:[A-Z]{{4,}}:)|$)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                if content:
                    return content
        return None

    # Get all sections from evaluation
    summary = extract_section(evaluation_text, ["SUMMARY", "OVERVIEW", "PERFORMANCE"])
    strengths = extract_section(
        evaluation_text, ["STRENGTHS", "STRONG POINTS", "POSITIVES"]
    )
    areas_to_improve = extract_section(
        evaluation_text, ["AREAS_TO_IMPROVE", "WEAKNESSES", "AREAS FOR IMPROVEMENT"]
    )
    actionable_tips = extract_section(
        evaluation_text, ["ACTIONABLE_TIPS", "TIPS", "ADVICE", "RECOMMENDATIONS"]
    )
    scores_section = extract_section(
        evaluation_text, ["SCORES", "RATINGS", "EVALUATION"]
    )

    # Extract scores
    scores = {}
    if scores_section:
        score_patterns = {
            "Technical": [r"Technical:?\s*(\d+)", r"Technical\s*Skills:?\s*(\d+)"],
            "Communication": [
                r"Communication:?\s*(\d+)",
                r"Communication\s*Skills:?\s*(\d+)",
            ],
            "Problem Solving": [
                r"Problem\s*Solving:?\s*(\d+)",
                r"Problem-Solving:?\s*(\d+)",
            ],
        }

        for category, patterns in score_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, scores_section, re.IGNORECASE)
                if match:
                    try:
                        score = int(match.group(1))
                        if 1 <= score <= 10:
                            scores[category] = score
                            break
                    except (ValueError, IndexError):
                        pass

    # Provide sample data if needed
    if not scores:
        scores = {"Technical": 7, "Communication": 6, "Problem Solving": 6}

    if not summary:
        summary = "The candidate demonstrated solid technical knowledge and communication skills during the interview. There were some areas where responses could have been more detailed, but overall, the interview showed good potential."

    if not strengths:
        strengths = "1. Clear communication with well-structured responses\n2. Good technical knowledge\n3. Professional demeanor throughout the interview"

    if not areas_to_improve:
        areas_to_improve = "1. Could provide more detailed technical explanations\n2. Sometimes responses were too general\n3. Could demonstrate more specific examples"

    if not actionable_tips:
        actionable_tips = "Research the company thoroughly before interviews and prepare specific work examples that directly relate to the position. Practice technical questions with more precision and depth. Consider recording yourself in mock interviews to identify areas for improvement."

    # Apply global styles
    st.markdown(
        """
    <style>
    .report-container {
        max-width: 1000px;
        margin: 0 auto;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    .report-header {
        text-align: center;
        margin-bottom: 30px;
    }
    .report-title {
        font-size: 28px;
        font-weight: 700;
        color: #2d3748;
        margin-bottom: 8px;
    }
    .report-subtitle {
        font-size: 16px;
        color: #718096;
    }
    .report-card {
        background: white;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    .card-title {
        font-size: 18px;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid #edf2f7;
    }
    .score-grid {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        gap: 20px;
        margin-bottom: 20px;
        width: 100%;
    }
    .score-card {
        background-color: #e6edf7;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        flex: 1;
        width: 30%;
    }
    .score-title {
        color: #4a5568;
        font-size: 16px;
        font-weight: 500;
        margin-bottom: 10px;
    }
    .score-value {
        font-size: 36px;
        font-weight: 700;
        color: #2d3748;
        margin: 15px 0;
    }
    .score-bar-bg {
        width: 100%;
        height: 6px;
        background-color: rgba(255,255,255,0.5);
        border-radius: 3px;
        margin: 15px 0 0 0;
    }
    .score-bar-fill {
        height: 100%;
        background-color: #4776E6;
        border-radius: 3px;
    }
    .point-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 30px;
    }
    .point-section {
        margin-bottom: 20px;
    }
    .point-title {
        font-size: 16px;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 15px;
    }
    .point-list {
        list-style-type: none;
        padding: 0;
        margin: 0;
    }
    .point-item {
        display: flex;
        margin-bottom: 15px;
        align-items: flex-start;
    }
    .point-icon {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        margin-right: 12px;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
    }
    .strength-icon {
        background-color: #38a169;
    }
    .improve-icon {
        background-color: #ed8936;
    }
    .point-text {
        flex-grow: 1;
        line-height: 1.5;
        color: #4a5568;
    }
    .tips-box {
        background-color: #f7fafc;
        border-left: 4px solid #4776E6;
        padding: 20px;
        border-radius: 4px;
        color: #4a5568;
        line-height: 1.6;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Begin report container
    st.markdown(
        """
    <div class="report-container">
        <div class="report-header">
            <h1 class="report-title">Interview Performance Report</h1>
            <p class="report-subtitle">Detailed analysis of your interview performance</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Summary card
    st.markdown(
        f"""
    <div class="report-card">
        <h2 class="card-title">Performance Summary</h2>
        <p>{summary}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Score cards - Using native Streamlit components
    st.markdown(
        """
    <div class="report-card">
        <h2 class="card-title">Performance Scores</h2>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Create columns for the three score cards with dividers between them
    col1, div1, col2, div2, col3 = st.columns([6, 0.5, 6, 0.5, 6])

    # Technical score card
    with col1:
        tech_score = scores.get("Technical", 7)
        st.markdown(
            f"<h3 style='text-align: center; color: #4a5568; font-size: 18px; font-weight: 500;'>Technical</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='text-align: center; font-size: 36px; font-weight: 700; color: #2d3748; margin: 10px 0;'>{tech_score}/10</p>",
            unsafe_allow_html=True,
        )
        st.progress(tech_score / 10)

    # First divider
    with div1:
        st.markdown(
            "<div style='width: 3px; background-color: #94a3b8; height: 120px; margin: auto; margin-top: 30px;'></div>",
            unsafe_allow_html=True,
        )

    # Communication score card
    with col2:
        comm_score = scores.get("Communication", 6)
        st.markdown(
            f"<h3 style='text-align: center; color: #4a5568; font-size: 18px; font-weight: 500;'>Communication</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='text-align: center; font-size: 36px; font-weight: 700; color: #2d3748; margin: 10px 0;'>{comm_score}/10</p>",
            unsafe_allow_html=True,
        )
        st.progress(comm_score / 10)

    # Second divider
    with div2:
        st.markdown(
            "<div style='width: 3px; background-color: #94a3b8; height: 120px; margin: auto; margin-top: 30px;'></div>",
            unsafe_allow_html=True,
        )

    # Problem Solving score card
    with col3:
        prob_score = scores.get("Problem Solving", 6)
        st.markdown(
            f"<h3 style='text-align: center; color: #4a5568; font-size: 18px; font-weight: 500;'>Problem Solving</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='text-align: center; font-size: 36px; font-weight: 700; color: #2d3748; margin: 10px 0;'>{prob_score}/10</p>",
            unsafe_allow_html=True,
        )
        st.progress(prob_score / 10)

    # Strengths and areas to improve
    if strengths or areas_to_improve:
        # Parse points
        strength_points = re.split(r"(?:\d+\.\s*|\n+)", strengths) if strengths else []
        strength_points = [s.strip() for s in strength_points if s.strip()]

        improve_points = (
            re.split(r"(?:\d+\.\s*|\n+)", areas_to_improve) if areas_to_improve else []
        )
        improve_points = [w.strip() for w in improve_points if w.strip()]

        # Generate strengths and weaknesses HTML
        st.markdown(
            """
        <div class="report-card">
            <h2 class="card-title">Strengths & Areas for Improvement</h2>
            <div class="point-grid">
        """,
            unsafe_allow_html=True,
        )

        # Strengths column
        st.markdown(
            """
        <div class="point-section">
            <h3 class="point-title">Key Strengths</h3>
            <ul class="point-list">
        """,
            unsafe_allow_html=True,
        )

        for point in strength_points[:3]:
            st.markdown(
                f"""
            <li class="point-item">
                <div class="point-icon strength-icon">✓</div>
                <div class="point-text">{point}</div>
            </li>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("</ul></div>", unsafe_allow_html=True)

        # Areas to improve column
        st.markdown(
            """
        <div class="point-section">
            <h3 class="point-title">Areas for Growth</h3>
            <ul class="point-list">
        """,
            unsafe_allow_html=True,
        )

        for point in improve_points[:3]:
            st.markdown(
                f"""
            <li class="point-item">
                <div class="point-icon improve-icon">!</div>
                <div class="point-text">{point}</div>
            </li>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("</ul></div></div></div>", unsafe_allow_html=True)

    # Actionable tips
    if actionable_tips:
        st.markdown(
            f"""
        <div class="report-card">
            <h2 class="card-title">Actionable Tips for Future Interviews</h2>
            <div class="tips-box">
                {actionable_tips}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Close report container
    st.markdown("</div>", unsafe_allow_html=True)


def extract_section(text, section_name):
    """Extract a section from the evaluation text using a more reliable pattern"""
    pattern = rf"{section_name}:?\s*(.*?)(?:(?:[A-Z]{{5,}})|$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None
