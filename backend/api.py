from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import os
import shutil
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

app = FastAPI(title = "Meeting Notes Summariser API")

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

load_dotenv()

DB_DIRECTORY = os.getenv("DB_DIRECTORY", "./meeting_chroma_db")

print("1. Loading Embedding Model and Vector Database...")

embedding_model = HuggingFaceEmbeddings(model_name = "all-MiniLM-L6-v2")
vector_db = Chroma(
    persist_directory = DB_DIRECTORY,
    embedding_function = embedding_model
)

print("2. Connecting to local ollama (phi3)...")
llm = ChatOllama(model = "phi3")
retriever = vector_db.as_retriever(
    search_type = "mmr",
    search_kwargs = {"k": 5, "fetch_k": 20}
)

print("3. Building Conversational Memory Chains...")

contextualise_q_system_prompt = (
    "Given a chat history and a latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. DO NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

contextualise_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualise_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualise_q_prompt
)

qa_system_prompt = (
    "You are an expert executive assistant and meeting analyst. "
    "You are answering questions based on raw, unstructured meeting transcripts.\n"
    "Because these are conversational transcripts, you must read between the lines, "
    "synthesize fragmented discussions, and ignore conversational filler.\n"
    "Use the provided context to answer the user's question comprehensively. "
    "If the context does not contain the answer, explicitly say 'I don't have enough information in these transcripts. "
    "If someone asks questions related to any other topic, politely decline to answer. "
    "Dates in the meeting transcripts are in the format yyyy-mm-dd. "
    "Always reference the meeting dates in your response if applicable.\n\n"
    "Context: {context}"
)

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", qa_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

doc_prompt = PromptTemplate(
    input_variables = ["page_content", "title"],
    template = "Meeting: {title}\nTranscript Excerpt:\n{page_content}"
)

question_answer_chain = create_stuff_documents_chain(
    llm = llm, 
    prompt = qa_prompt,
    document_prompt = doc_prompt
)

rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    chat_history: List[Message] = []

@app.post("/api/chat")
async def chat(request: ChatRequest):
     
     langchain_history = []
     for msg in request.chat_history:
         if msg.role == "user":
             langchain_history.append(HumanMessage(content = msg.content))
         else:
             langchain_history.append(AIMessage(content = msg.content))
     
     response = rag_chain.invoke({
         "input": request.query,
         "chat_history": langchain_history
         })

     sources = []
     for doc in response["context"]:
         sources.append({
             "title": doc.metadata.get("title", "Meeting Transcript"),
             "content": doc.page_content[:150] + "..."
            })

     return {
         "answer": response["answer"],
         "sources": sources
     }

class TitleRequest(BaseModel):
    query: str

@app.post('/api/title')
async def generate_title(request: TitleRequest):
    print("Generating Dynamic Title...")

    title_prompt = PromptTemplate.from_template(
        "You are an expert copywriter. Generate a highly concise 3 to 5 word title "
        "for a conversation that begins with the following user prompt. "
        "Return ONLY the title string. Do not use quotes, punctuations or conversational filler.\n\n"
        "User Prompt: {query}"
    )  

    title_chain = title_prompt | llm

    generated_title = title_chain.invoke({ "query": request.query })

    clean_title = generated_title.replace('"', '').replace("'", "").strip()

    return { "title": clean_title }

@app.post('/api/upload')
async def upload_transcript(file: UploadFile = File(...)):
    print(f"Receiving file: {file.filename}")

    data_dir = os.getenv("DATA_DIRECTORY", "./transcripts")
    os.makedirs(data_dir, exist_ok = True)
    file_path = os.path.join(data_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    print("Processing Text...")
    loader = TextLoader(file_path, encoding = 'utf-8')
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 2500,
        chunk_overlap = 500,
        length_function = len
    )

    chunks = text_splitter.split_documents(documents)
    clean_title = file.filename.replace('.txt', '').replace('_', ' ')
    for chunk in chunks:
        if not chunk.metadata:
            chunk.metadata = {}
        chunk.metadata['title'] = clean_title
        chunk.metadata['type'] = 'Meeting Transcript'
    
    print(f"Adding {len(chunks)} chunks to the vector database...")
    vector_db.add_documents(chunks)

    return {
        "status": "success",
        "message": f"Successfully processed '{clean_title}' and added to the memory."
    }