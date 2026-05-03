from fastapi import FastAPI
from pydantic import BaseModel
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains import create_history_aware_retriever
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from langchain_core.messages import HumanMessage, AIMessage

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
retriever = vector_db.as_retriever(search_kwargs = {"k": 10})

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
    "You are an AI meeting transcript summariser. Use the following context from meeting transcripts "
    "to answer the user's question. If you do not know the answer, say you don't know. "
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

doc_prompt = PromptTemplate.from_template(
    "Meeting date: {date}\nTranscript Excerpt: {page_content}"
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
             "date": doc.metadata.get("date"),
             "meeting_uid": doc.metadata.get("meeting_uid"),
             "summary": doc.metadata.get("summary")
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