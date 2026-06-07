import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.3-70b-versatile"

# --- Embeddings ---
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# --- Vector store ---
CHROMA_COLLECTION = "unofficial_guide"
CHROMA_PATH = "./chroma_db"

# --- Retrieval ---
N_RESULTS = 5
RETRIEVAL_MODE = os.getenv("RETRIEVAL_MODE", "semantic")  # "semantic" or "hybrid"
HYBRID_CANDIDATE_POOL = 20
HYBRID_RRF_K = 60

# --- Documents ---
RAW_PATH = "./raw"           # raw RMP PDFs and other unprocessed sources
RAW_TEXT_PATH = "./raw_text" # pdfplumber output before cleaning
DOCS_PATH = "./documents"    # processed .txt — read by load_documents(), written by preprocess_pdfs()
