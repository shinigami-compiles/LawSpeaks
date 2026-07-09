"""
NYAYAGPT – Global Configuration File

This file centralizes all configuration values used across the project.
Changing paths, models, or API behavior should be done ONLY here.

Safe for:
- Windows
- CPU-only systems
- Low-RAM machines
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# --------------------------------------------------
# Load Environment Variables
# --------------------------------------------------

# Loads variables from a .env file if present
# Example .env:
# MISTRAL_API_KEY=your_api_key_here
load_dotenv()

# --------------------------------------------------
# BASE PROJECT PATH
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

# --------------------------------------------------
# DATA DIRECTORIES
# --------------------------------------------------

DATA_DIR = BASE_DIR / "data"

STATUTES_DIR = DATA_DIR / "statutes"     # IPC, CrPC, Acts, Constitution
JUDGMENTS_DIR = DATA_DIR / "judgments"   # Supreme Court judgments
QA_DIR = DATA_DIR / "qa"                 # IndicLegalQA / Indian Law QA

# Preprocessed output
PROCESSED_DATA_DIR = DATA_DIR / "processed"
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# EMBEDDINGS & FAISS CONFIG
# --------------------------------------------------

# Sentence-Transformer model (lightweight & CPU-friendly)
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# FAISS index storage
FAISS_INDEX_PATH = BASE_DIR / "embeddings" / "faiss_index.bin"
FAISS_METADATA_PATH = BASE_DIR / "embeddings" / "faiss_metadata.json"

# Embedding parameters
EMBEDDING_DIMENSION = 384        # Fixed for MiniLM
FAISS_TOP_K = 5                 # Number of chunks retrieved per query

# --------------------------------------------------
# TEXT CHUNKING CONFIG
# --------------------------------------------------

# Chunk size should balance:
# - Enough legal context
# - Not too large for LLM input
CHUNK_SIZE = 500        # characters
CHUNK_OVERLAP = 100     # characters

# --------------------------------------------------
# Groq LLM API CONFIG
# --------------------------------------------------

GROK_API_KEY = os.getenv("GROK_API_KEY")

if not GROK_API_KEY:
    print("WARNING: GROK_API_KEY not found")

GROK_API_URL = "https://api.groq.com/openai/v1/chat/completions"

GROK_MODEL_NAME = "llama-3.3-70b-versatile"   # or "grok-beta"


# Token & generation control
MAX_TOKENS = 500
TEMPERATURE = 0.2         # Low temperature for legal accuracy
TOP_P = 0.9

# --------------------------------------------------
# FASTAPI CONFIG
# --------------------------------------------------

API_HOST = "0.0.0.0"
API_PORT = 8000

# --------------------------------------------------
# SAFETY & LEGAL DISCLAIMER
# --------------------------------------------------

LEGAL_DISCLAIMER = (
    "⚠️ Disclaimer: This information is for legal awareness only and "
    "does not constitute legal advice. For legal action, consult a "
    "qualified lawyer or appropriate authority."
)

# --------------------------------------------------
# LOGGING (Simple & Lightweight)
# --------------------------------------------------

LOG_LEVEL = "INFO"

# --------------------------------------------------
# RISK & URGENCY THRESHOLDS (Rule-Based)
# --------------------------------------------------

RISK_LEVELS = {
    "LOW": {
        "description": "Minor legal issue, no immediate danger",
        "recommended_action": "Understand rights and monitor situation"
    },
    "MEDIUM": {
        "description": "Potential legal consequences if ignored",
        "recommended_action": "Seek legal guidance or file complaint"
    },
    "HIGH": {
        "description": "Serious legal risk or rights violation",
        "recommended_action": "Immediate legal action recommended"
    }
}

# --------------------------------------------------
# END OF CONFIG
# --------------------------------------------------


print("=" * 50)
print("LawSpeaks Configuration Loaded")
print(f"BASE_DIR: {BASE_DIR}")
print(f"FAISS INDEX: {FAISS_INDEX_PATH}")
print(f"METADATA: {FAISS_METADATA_PATH}")
print("=" * 50)