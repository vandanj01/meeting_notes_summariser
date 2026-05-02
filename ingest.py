import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

def process_meeting_data(csv_path):
    print("1. Loading CSV Data...")
    df = pd.read_csv(csv_path).fillna("")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,
        chunk_overlap = 200,
        length_function = len,
    )

    all_documents = []

    print("2. Chunking transscript and attaching metadata...")
    for index, row in df.iterrows():
        transcript_text = str(row['Transcript'])

        if not transcript_text.strip():
            continue

        metadata = {
            "date": row['Date'],
            "meeting_uid": row['Meeting_UID'],
            "item_uid": row['Item_UID'],
            "summary": row['Summary'],
        }

        chunks = text_splitter.split_text(transcript_text)

        for chunk in chunks:
            doc = Document(
                page_content = chunk,
                metadata = metadata
            )
            all_documents.append(doc)
        
    print(f"Success! Processed {len(df)} meeting into {len(all_documents)} searchable chunks.")
    return all_documents

def build_vector_database(documents):
    print("3. Loading embedding model (this will download ~90 MB the first time)...")
    embedding_model = HuggingFaceEmbeddings(model_name = "all-MiniLM-L6-v2")

    db_folder = "./meeting_chroma_db"

    print(f"4. Converting text to vectors and saving to {db_folder}...")
    print(" (This may take a minute or two depending on your CSV size...)")

    vector_db = Chroma.from_documents(
        documents = documents,
        embedding = embedding_model,
        persist_directory = db_folder
    )

    print(f"Success! Your local vector database is ready at '{db_folder}'.")
    return vector_db

if __name__ == "__main__":
    docs = process_meeting_data("./dataset/test_df.csv")
    db = build_vector_database(docs)