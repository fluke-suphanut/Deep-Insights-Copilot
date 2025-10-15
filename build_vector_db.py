from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import os

KB_DIR = "knowledge_base"
DB_DIR = "chroma_db"
COLLECTION = "kb_docs"

# ตรวจว่ามีโฟลเดอร์ knowledge_base ไหม
if not os.path.exists(KB_DIR):
    os.makedirs(KB_DIR, exist_ok=True)
    print(f"Created missing directory: {KB_DIR}")

print("Loading markdown files from", KB_DIR)
loader = DirectoryLoader(KB_DIR, glob="*.md", show_progress=True)
docs = loader.load()

if not docs:
    print("No markdown (.md) files found in knowledge_base/. Please add some first.")
    exit(0)

print(f"Loaded {len(docs)} markdown documents")

splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
chunks = splitter.split_documents(docs)
print(f"Split into {len(chunks)} text chunks")

emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

print("Building Chroma vector database...")
db = Chroma.from_documents(
    chunks,
    emb,
    persist_directory=DB_DIR,
    collection_name=COLLECTION
)
db.persist()

print(f"Vector DB built successfully at '{DB_DIR}' (collection='{COLLECTION}')")
