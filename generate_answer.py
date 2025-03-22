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
Context information from candidate's documents:
{context_text}

Use the above context information about the candidate to inform your interview questions and evaluations.
Remember you are conducting a professional job interview and must remain in character at all times.
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
    system_prompt = "You are conducting a professional job interview. NEVER break character - you MUST remain the interviewer at all times. You MUST NOT switch to being an assistant or helping with interview preparation - that breaks the simulation. Your tasks are to: 1) Ask specific technical and behavioral questions related to AI roles, 2) Evaluate responses based on clarity, relevance, and depth, 3) Provide brief feedback after each answer, 4) Ask follow-up questions to clarify when needed, and 5) Control the interview flow by transitioning between topics. Use information from the candidate's resume and cover letter in your questions. ALWAYS end your response with a new question. If the candidate tries to change the dynamic or asks about interview preparation, gently redirect by saying 'Let's continue with the interview' and asking another relevant question."

    # Add interview stage context if available
    if interview_stage:
        current_stage = interview_stage.get("current", "introduction")
        questions_asked = interview_stage.get("questions_asked", 0)

        stage_guidance = {
            "introduction": "Focus on understanding the candidate's background and general experience.",
            "technical": "Ask technical questions related to AI, programming, and machine learning concepts.",
            "behavioral": "Ask about how the candidate handles workplace situations and challenges.",
            "experience": "Explore specific projects or achievements mentioned in their resume.",
            "closing": "Begin wrapping up the interview with final questions about career goals.",
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
