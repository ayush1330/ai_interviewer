# AI Interview Assistant

## Overview
The AI Interview Assistant is a web application designed to help users prepare for job interviews by simulating interview scenarios. It leverages OpenAI's language models to provide real-time feedback, generate performance evaluations, and create podcast-style summaries of interview sessions.

## Features
- **Interview Simulation**: Conducts mock interviews with a focus on technical and behavioral questions.
- **Performance Evaluation**: Generates comprehensive evaluations based on user responses, highlighting strengths and areas for improvement.
- **Podcast Generation**: Creates audio summaries of interview evaluations, allowing users to listen to their performance feedback.
- **Document Upload**: Users can upload resumes and cover letters to tailor the interview experience.
- **Speech Recognition**: Converts spoken responses into text for analysis and evaluation.

## Installation
1. Clone the repository:
   ```bash
   git clone 
   cd ai-interview-assistant
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the root directory and add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

## Usage
1. Run the application:
   ```bash
   streamlit run app.py
   ```

2. Follow the on-screen instructions to upload your documents and start the interview.

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

