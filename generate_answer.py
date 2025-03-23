import os
from glob import glob
from typing import List

import openai
from openai import OpenAI
from dotenv import load_dotenv

from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.memory import ConversationBufferMemory

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)
openai.api_key = api_key


class VectorDB:
    """Class to manage document loading and vector database creation."""

    def __init__(self, pdf_paths: List[str]):
        self.pdf_paths = pdf_paths
        self.vector_store = self.create_vector_db()

    def create_vector_db(self):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100
        )

        # Load and split each PDF document
        pdf_docs = []
        for pdf_path in self.pdf_paths:
            loader = PyPDFLoader(pdf_path)
            pdf_docs.extend(loader.load())
        chunks = text_splitter.split_documents(pdf_docs)

        return Chroma.from_documents(chunks, OpenAIEmbeddings())


class ConversationalRetrievalChain:
    """Class to manage the interview chain setup."""

    def __init__(self, model_name="gpt-4o", temperature=0):
        self.model_name = model_name
        self.temperature = temperature

    def create_chain(self, vector_db: VectorDB):
        self.model = ChatOpenAI(
            model_name=self.model_name,
            temperature=self.temperature,
        )

        self.retriever = vector_db.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3},
        )

        return self

    def __call__(self, query_dict):
        user_query = query_dict["query"]

        # Search for relevant documents
        docs = self.retriever.get_relevant_documents(user_query)

        # Format the retrieved context
        context_text = "\n\n".join([doc.page_content for doc in docs])

        # Format the complete prompt with context
        formatted_prompt = f"""
Context information from the candidate's documents:
{context_text}

Use the above context information to guide your questions and responses. 
Focus on the candidate's relevant skills, experiences, and achievements. 
You are conducting a professional job interview—remain in character, 
maintain a respectful and unbiased tone, and adapt your questions 
to the details provided here.
"""

        # Add formatted_prompt to user_query if not empty
        if context_text.strip():
            full_query = {
                "role": "user",
                "content": formatted_prompt + "\n\nUser message: " + user_query,
            }
        else:
            full_query = {"role": "user", "content": user_query}

        # Get messages including the system message
        # (which should be at messages[0]["content"] passed by the conduct_interview function)
        messages = query_dict.get("messages", [])

        completion = self.model.invoke(messages + [full_query])

        return {"result": completion.content}


def conduct_interview(messages, vector_db: VectorDB, interview_stage=None):
    """Main function to execute the interview with context and retrieval."""
    # Define the system message to guide the LLM
    system_prompt = ("You are conducting a professional job interview."
                    "Your role is to remain strictly the interviewer throughout"
                    "the session—do not offer interview preparation or deviate"
                    "from your role."
                    "Your primary tasks are:"
                    "1. Ask both technical and behavioral questions that are relevant"
                        "to the candidate's background."
                    "2. Evaluate each response based on clarity, relevance, and depth,"
                        "and provide brief, constructive feedback."
                    "3. Always end your response with a new, open-ended question to keep" 
                        "the conversation flowing."
                    "4. If the candidate attempts to change the dynamic or requests advice"
                        "unrelated to the interview, gently redirect by stating, 'Let's continue with the interview.'"
                    "5. Maintain a respectful, neutral, and professional tone at all times,"
                        "avoiding any bias or discriminatory language."
                    "6. Use the candidate's background context (e.g., resume and cover letter details)" 
                        "to tailor your questions, but be prepared to explore new topics as the conversation evolves."
                    "7. If any response is vague or ambiguous, ask clarifying follow-up questions to ensure a full understanding."
                    "Follow these guidelines consistently to ensure that the interview is structured, unbiased, and productive.")

    # Add interview stage context if available
    if interview_stage:
        current_stage = interview_stage.get("current", "introduction")
        questions_asked = interview_stage.get("questions_asked", 0)

        stage_guidance = {"The interview is divided into five stages. Use the"
                        "candidate's background to customize your questions,"
                        "ensure smooth transitions, and delve deeply into each"
                        "area without excessive repetition. Proceed as follows:"
                        "1.Introduction: Establish rapport and gather general background,"
                        "  inviting the candidate to share their journey and inspiration in their field."
                        "2.Technical: Focus on core skills and projects by exploring specific technical"
                        "  challenges and problem-solving approaches relevant to their expertise."
                        "3.Behavioral: Investigate soft os.kill and interpersonal experiences by "
                        "  examining how the candidate handled teamwork, conflict, and leadership situations."
                        "4.Experience: Explore details from the candidate’s resume and cover letter, highlighting"
                        "  key achievements and the strategies behind them."
                        "5.Closing: Summarize the discussion and invite reflection on future goals,"
                        "  ensuring an opportunity for the candidate to share any final thoughts."
                        "Maintain a respectful, neutral, and professional tone throughout. Adapt"
                        "follow-up questions based on the candidate’s responses and pivot when relevant"
                        "to explore interesting threads, rather than strictly following the stage boundaries."
        }

        system_prompt += f"\n\nCurrent interview stage: {current_stage}. {stage_guidance.get(current_stage, '')} You have asked {questions_asked} questions so far in this stage."

    # Create the system message
    system_message = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    # Get just the user and assistant messages for context
    user_messages = []
    for msg in messages:
        if msg["role"] in ["user", "assistant"]:
            user_messages.append(msg)

    # Get the last user message to use as the query
    query = messages[-1]["content"].strip()

    # Initialize the conversational retrieval chain
    qa_chain = ConversationalRetrievalChain().create_chain(vector_db)

    # Pass both the system message and context messages to the chain
    result = qa_chain({"query": query, "messages": system_message + user_messages})

    return result["result"]