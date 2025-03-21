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


def base_model_chatbot(messages):
    system_message = [
        {
            "role": "system",
            "content": "You are an AI interviewer for AI-related and behavioral roles. Ask interview questions, evaluate candidate responses, and provide constructive feedback. Adapt your follow-up questions based on the candidate's previous answers.",
        }
    ]
    messages = system_message + messages
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106", messages=messages
    )
    return response.choices[0].message.content


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
    """Class to manage the QA chain setup."""

    def __init__(self, model_name="gpt-3.5-turbo", temperature=0):
        self.model_name = model_name
        self.temperature = temperature

    def create_chain(self, vector_db: VectorDB):
        model = ChatOpenAI(
            model_name=self.model_name,
            temperature=self.temperature,
        )

        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )
        retriever = vector_db.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 2},
        )
        return RetrievalQA.from_chain_type(
            llm=model,
            retriever=retriever,
            memory=memory,
        )


def with_pdf_chatbot(messages, vector_db: VectorDB):
    """Main function to execute the QA system."""
    query = messages[-1]["content"].strip()

    qa_chain = ConversationalRetrievalChain().create_chain(vector_db)
    result = qa_chain({"query": query})
    return result["result"]
