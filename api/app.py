"""
NYAYAGPT – FastAPI Backend

Purpose:
- Expose REST APIs for all 7 legal-awareness features
- Connect frontend → RAG generator → Mistral LLM
- Enforce safe, structured responses

Run:
    uvicorn api.app:app --reload
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from rag.generator import LegalRAGGenerator
from config import API_HOST, API_PORT
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
# --------------------------------------------------
# FASTAPI APP INITIALIZATION
# --------------------------------------------------

app = FastAPI(
    title="NYAYAGPT – Indian Legal Self-Defense Assistant",
    description=(
        "A Retrieval-Augmented Generation (RAG) based legal awareness system "
        "for Indian citizens. This system provides legal awareness, "
        "not legal advice."
    ),
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent.parent

STICH_DIR = BASE_DIR / "stich"
ASSETS_DIR = STICH_DIR / "assets"

print("=" * 50)
print("LawSpeaks Startup Check")
print(f"BASE_DIR: {BASE_DIR}")
print(f"STICH_DIR Exists: {STICH_DIR.exists()}")
print(f"ASSETS_DIR Exists: {ASSETS_DIR.exists()}")
print("=" * 50)

app.mount(
    "/stich",
    StaticFiles(directory=str(STICH_DIR)),
    name="stich"
)
from fastapi.staticfiles import StaticFiles

app.mount(
    "/assets",
    StaticFiles(directory=str(ASSETS_DIR)),
    name="assets"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-app.onrender.com"],   # allow all (for development)
    allow_credentials=True,
    allow_methods=["*"],   # allow POST, GET, OPTIONS
    allow_headers=["*"],
)

# Initialize RAG Generator (loads FAISS + MiniLM once)
rag_generator = LegalRAGGenerator()

# --------------------------------------------------
# REQUEST SCHEMAS
# --------------------------------------------------

class AskRequest(BaseModel):
    query: str = Field(
        min_length=3,
        max_length=1000
    )

class RightsRequest(BaseModel):
    category: str = Field(
        min_length=3,
        max_length=1000
    )

class ActionGuideRequest(BaseModel):
    action_type: str = Field(
        min_length=3,
        max_length=1000
    )


class CaseRequest(BaseModel):
    issue: str = Field(
        min_length=3,
        max_length=1000
    )


class LawLibraryRequest(BaseModel):
    law_query: str = Field(
        min_length=3,
        max_length=1000
    )

class SituationRequest(BaseModel):
    situation_details: str = Field(
        min_length=3,
        max_length=1000
    )


class RiskRequest(BaseModel):
    issue: str = Field(
        min_length=3,
        max_length=1000
    )


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/")
def serve_home():
    return FileResponse(str(STICH_DIR / "index.html"))


# --------------------------------------------------
# FEATURE 1: ASK A LEGAL QUESTION
# --------------------------------------------------

@app.post("/ask")
def ask_legal_question(request: AskRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    response = rag_generator.ask_legal_question(request.query)
    return {"response": response}


# --------------------------------------------------
# FEATURE 2: KNOW YOUR RIGHTS
# --------------------------------------------------

@app.post("/rights")
def know_your_rights(request: RightsRequest):
    if not request.category.strip():
        raise HTTPException(status_code=400, detail="Category cannot be empty")

    response = rag_generator.know_your_rights(request.category)
    return {"response": response}


# --------------------------------------------------
# FEATURE 3: LEGAL ACTION GUIDE
# --------------------------------------------------

@app.post("/action-guide")
def legal_action_guide(request: ActionGuideRequest):
    if not request.action_type.strip():
        raise HTTPException(status_code=400, detail="Action type cannot be empty")

    response = rag_generator.legal_action_guide(request.action_type)
    return {"response": response}


# --------------------------------------------------
# FEATURE 4: CASE EXAMPLES
# --------------------------------------------------

@app.post("/cases")
def case_examples(request: CaseRequest):
    if not request.issue.strip():
        raise HTTPException(status_code=400, detail="Issue cannot be empty")

    response = rag_generator.case_examples(request.issue)
    return {"response": response}


# --------------------------------------------------
# FEATURE 5: LAW LIBRARY
# --------------------------------------------------

@app.post("/library")
def law_library(request: LawLibraryRequest):
    if not request.law_query.strip():
        raise HTTPException(status_code=400, detail="Law query cannot be empty")

    response = rag_generator.law_library(request.law_query)
    return {"response": response}


# --------------------------------------------------
# FEATURE 6: MY LEGAL SITUATION (FORM-BASED)
# --------------------------------------------------

@app.post("/situation")
def my_legal_situation(request: SituationRequest):
    if not request.situation_details.strip():
        raise HTTPException(status_code=400, detail="Situation details cannot be empty")

    response = rag_generator.my_legal_situation(request.situation_details)
    return {"response": response}


# --------------------------------------------------
# FEATURE 7: RISK & URGENCY CHECKER
# --------------------------------------------------

@app.post("/risk-check")
def risk_and_urgency(request: RiskRequest):
    if not request.issue.strip():
        raise HTTPException(status_code=400, detail="Issue cannot be empty")

    response = rag_generator.risk_and_urgency(request.issue)
    return {"response": response}


# --------------------------------------------------
# RUN LOCALLY (OPTIONAL)
# --------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.app:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )
