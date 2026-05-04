import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader

load_dotenv()

DATA_DIRECTORY = os.getenv("DATA_DIRECTORY", "./transcripts")
DB_DIRECTORY = os.getenv("DB_DIRECTORY", "./meeting_chroma_db")

def ingest_data():
    print("1. Loading embedding model (this will download ~90 MB the first time)...")
    embedding_model = HuggingFaceEmbeddings(model_name = "all-MiniLM-L6-v2")

    print(f"2. Loading text transcripts from '{DATA_DIRECTORY}'...")
    loader = DirectoryLoader('./transcripts', glob = "**/*.txt", loader_cls = TextLoader, loader_kwargs = { 'encoding': 'utf-8' })
    documents = loader.load()

    if not documents:
        print("No text files found.")
        return
    
    print(f"Loaded {len(documents)} transcript files.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 2500,
        chunk_overlap = 500,
        length_function = len,
    )

    print("3. Chunking transscript and attaching metadata...")

    chunks = text_splitter.split_documents(documents)

    for chunk in chunks:
        file_path = chunk.metadata.get('source', '')
        file_name = os.path.basename(file_path)
        clean_title = file_name.replace('.txt', '').replace('_', ' ')
        chunk.metadata['title'] = clean_title
        chunk.metadata['type'] = 'Meeting Transcript'

    print(f"Success! Processed {len(documents)} meetings into {len(chunks)} searchable chunks.")

    print(f"4. Converting text to vectors and saving to {DB_DIRECTORY}...")
    print(" (This may take a minute or two depending on your dataset size...)")

    vector_db = Chroma.from_documents(
        documents = chunks,
        embedding = embedding_model,
        persist_directory = DB_DIRECTORY
    )

    print(f"Success! Your local vector database is ready at '{DB_DIRECTORY}'.")

    return vector_db

if __name__ == "__main__":
    ingest_data()