# AI Voice Interview Assistant

An interactive AI-powered interview preparation platform that conducts voice-based mock interviews, provides real-time feedback, and generates personalized podcast summaries.

## 🌟 Features

- **Voice-Based Interaction**: Natural conversation flow with voice input and output capabilities
- **Document Analysis**: Upload your resume and cover letter for personalized interview questions
- **Job Description Integration**: Tailor interviews based on specific job requirements
- **Real-time Feedback**: Get immediate feedback on your interview responses
- **Performance Evaluation**: Comprehensive assessment of your interview performance
- **Podcast Generation**: Convert your interview feedback into an audio podcast format
- **Multi-Stage Interview**: Covers introduction, technical, behavioral, experience, and closing segments

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip package manager
- Microphone for voice input
- Speakers/Headphones for audio output

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd ai_interviewer
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory and add your API keys:
```
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

4. Run the application:
```bash
streamlit run app.py
```

## 💡 Usage

1. **Upload Documents**:
   - Upload your resume (PDF format)
   - Upload your cover letter (PDF format)
   - Paste the job description you're targeting

2. **Start Interview**:
   - Click "Start Your Interview" to begin the session
   - Speak into your microphone to respond to questions
   - Listen to the AI interviewer's responses and follow-up questions

3. **Review Performance**:
   - Get detailed feedback on your interview performance
   - Generate a podcast summary of your interview
   - Listen to personalized improvement suggestions

## 🛠️ Technical Stack

- **Frontend**: Streamlit
- **AI/ML**: OpenAI GPT models
- **Speech-to-Text**: Whisper API
- **Text-to-Speech**: ElevenLabs
- **Vector Database**: ChromaDB
- **Document Processing**: PDF parsing tools

## 📝 Features in Detail

### Interview Stages
- Introduction
- Technical Assessment
- Behavioral Questions
- Experience Discussion
- Closing Remarks

### Document Analysis
- Resume parsing and understanding
- Cover letter analysis
- Job description matching
- Context-aware questioning

### Voice Processing
- Real-time voice input processing
- Natural text-to-speech output
- Clear audio playback

## 🔒 Privacy & Security

- Documents are processed temporarily and not stored permanently
- Session-based data handling
- Secure API integrations
- No persistent storage of user data

## 🎯 Project Structure

```
ai_interviewer/
├── app.py                 # Main Streamlit application
├── generate_answer.py     # Interview response generation
├── evaluation.py         # Performance evaluation logic
├── podcast_generator.py  # Podcast creation functionality
├── helpers.py           # Utility functions
├── utils/              # Additional utilities
├── requirements.txt    # Project dependencies
└── .env               # Environment variables
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


## 🙏 Acknowledgments

- OpenAI for GPT models
- ElevenLabs for voice synthesis
- Streamlit for the web framework
- All contributors and testers


## 🔄 Updates and Maintenance

- Regular updates for API compatibility
- Performance optimizations
- Bug fixes and improvements
- New feature additions

---

Made with ❤️ for job seekers and interviewers
