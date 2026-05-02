from fastapi import FastAPI
from pydantic import BaseModel
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import PromptTemplate
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title = "Meeting Notes Summariser API")

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

print("1. Loading Embedding Model and Vector Database...")

embedding_model = HuggingFaceEmbeddings(model_name = "all-MiniLM-L6-v2")
vector_db = Chroma(
    persist_directory = "./meeting_chroma_db",
    embedding_function = embedding_model
)

print("2. Connecting to local ollama (phi3)...")
llm = Ollama(model = "phi3")

print("3. Building the RAG pipeline...")

system_prompt = (
    "You are an AI meeting transcript summariser. Use the following context from meeting transcripts "
    "to answer the user's question. If you do not know the answer, say you don't know. "
    "If someone asks questions related to any other topic, politely decline to answer. "
    "Dates in the meeting transcripts are in the format yyyy-mm-dd. "
    "Always reference the meeting dates in your response if applicable.\n\n"
    "Context: {context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

doc_prompt = PromptTemplate.from_template(
    "Meeting date: {date}\nTranscript Excerpt: {page_content}"
)

document_chain = create_stuff_documents_chain(
    llm = llm, 
    prompt = prompt,
    document_prompt = doc_prompt
)

retriever = vector_db.as_retriever(search_kwargs = {"k": 10})
rag_chain = create_retrieval_chain(retriever, document_chain)

class ChatRequest(BaseModel):
    query: str

@app.post("/api/chat")
async def chat(request: ChatRequest):
     response = rag_chain.invoke({"input": request.query})

     answer = response["answer"]

     sources = []
     for doc in response["context"]:
         sources.append({
             "date": doc.metadata.get("date"),
             "meeting_uid": doc.metadata.get("meeting_uid"),
             "summary": doc.metadata.get("summary")
            })

     return {
         "answer": answer,
         "sources": sources
     }