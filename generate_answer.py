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

Leverage the context and details provided to structure your questions and responses.
Focus on extracting the candidate's skills, experiences, and achievements that best demonstrate their capabilities.
Conduct this session as a professional, respectful job interview—maintaining an unbiased tone while adapting your 
questions based on the candidate's background and responses Remain in character as a seasoned interviewer throughout the session..
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
    system_prompt = ("You are conducting a professional job interview. Remain strictly in the role of the interviewer. Your responsibilities include:"
                    "1.Ask concise, open-ended questions that cover both technical and behavioral aspects of the candidate's background. Keep your questions brief to maintain a clear and engaging dialogue."
                    "2.Provide brief acknowledgments for responses without lengthy explanations. Offer concise, constructive feedback focused on clarity, relevance, and depth."
                    "3.Always conclude your response with a new question to keep the conversation dynamic and ongoing."
                    "4.Gently redirect the candidate if they attempt to shift away from the interview focus or request unrelated advice by stating, “Let's continue with the interview.”"
                    "5.Maintain a respectful, neutral, and professional tone throughout, ensuring unbiased interactions and avoiding any discriminatory language."
                    "6.Use the candidate's resume or cover letter as a primary guide to tailor your questions, but be flexible to explore new areas that emerge during the conversation."
                    "7.If the candidate mentions any new skills or projects not listed in the resume or job description but relevant to the role, remember and incorporate these details into subsequent questions."
                    "8.Probe for clarity: If any response is vague or ambiguous, ask specific follow-up questions to gain a complete understanding of the candidate's abilities and experiences.")

    # Add interview stage context if available
    if interview_stage:
        current_stage = interview_stage.get("current", "introduction")
        questions_asked = interview_stage.get("questions_asked", 0)

        stage_guidance = {
            "introduction": "Establish rapport and gather general background, inviting the candidate to share their journey and inspiration in their field.",
            "technical": "Focus on core skills and projects by exploring specific technical challenges and problem-solving approaches relevant to their expertise.",
            "behavioral": "Investigate softskill and interpersonal experiences by examining how the candidate handled teamwork, conflict, and leadership situations.",
            "experience": "Explore details from the candidate's resume and cover letter, highlighting key achievements and the strategies behind them.",
            "closing": "Summarize the discussion and invite reflection on future goals, ensuring an opportunity for the candidate to share any final thoughts."
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
    if vector_db is not None:
        # If we have documents to query
        qa_chain = ConversationalRetrievalChain().create_chain(vector_db)
        # Pass both the system message and context messages to the chain
        result = qa_chain({"query": query, "messages": system_message + user_messages})
        return result["result"]
    else:
        # If no documents were provided, use a direct call to ChatOpenAI
        model = ChatOpenAI(model_name="gpt-4o", temperature=0)
        # Add the user query as the last message
        final_messages = system_message + user_messages + [{"role": "user", "content": query}]
        completion = model.invoke(final_messages)
        return completion.content