"""
NYAYAGPT – FINAL & VERIFIED DATA PREPROCESSING PIPELINE

SUPPORTED DATA:
- Supreme Court Judgments (PDFs in year-wise folders)
- IPC / CrPC / CPC / IEA / NIA (JSON with section_desc)
- IndicLegalQA (JSON)
- Indian Law QA (JSON array: Instruction / Response)
- Indian_SC_Chunked (TXT)

OUTPUT:
- data/processed/legal_chunks.json

RUN:
    python -m preprocessing.preprocess_data
"""

import json
import re
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

import fitz  # PyMuPDF

from config import (
    STATUTES_DIR,
    JUDGMENTS_DIR,
    QA_DIR,
    PROCESSED_DATA_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)

# --------------------------------------------------
# TEXT CLEANING
# --------------------------------------------------

def clean_text(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"Page \d+ of \d+", "", text, flags=re.I)
    text = re.sub(r"SUPREME COURT OF INDIA", "", text, flags=re.I)
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\(\d{4}\)\s*\d+\s*SCC\s*\d+", "", text)

    return text.strip()


# --------------------------------------------------
# CHUNKING
# --------------------------------------------------

def chunk_text(text: str) -> List[str]:
    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = start + CHUNK_SIZE
        chunk = text[start:end]

        if len(chunk.strip()) >= 80:
            chunks.append(chunk)

        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


# --------------------------------------------------
# PDF EXTRACTION
# --------------------------------------------------

def extract_text_from_pdf(pdf_path: Path) -> str:
    try:
        doc = fitz.open(pdf_path)
        pages = [page.get_text("text") for page in doc]
        return clean_text(" ".join(pages))
    except Exception as e:
        print(f"⚠️ Failed PDF: {pdf_path.name} → {e}")
        return ""


# --------------------------------------------------
# SUPREME COURT JUDGMENTS (PDF)
# --------------------------------------------------

def process_sc_judgments() -> List[Dict]:
    processed = []
    pdf_count = 0

    print("\n⚖️ Processing Supreme Court Judgments (PDFs)...")

    for year_dir in sorted(JUDGMENTS_DIR.iterdir()):
        if not year_dir.is_dir():
            continue

        year = year_dir.name

        for pdf_file in tqdm(year_dir.glob("*.pdf"), desc=f"SC {year}"):
            pdf_count += 1
            case_name = pdf_file.stem
            raw_text = extract_text_from_pdf(pdf_file)

            if not raw_text:
                continue

            for i, chunk in enumerate(chunk_text(raw_text)):
                processed.append({
                    "source": "judgment",
                    "court": "Supreme Court of India",
                    "year": year,
                    "case_name": case_name,
                    "chunk_id": i,
                    "text": chunk
                })

    print(f"✅ Supreme Court PDFs processed: {pdf_count}")
    print(f"✅ SC chunks generated: {len(processed)}")

    return processed


# --------------------------------------------------
# IPC / CrPC / CPC / IEA / NIA
# --------------------------------------------------

def process_statutes() -> List[Dict]:
    processed = []
    section_count = 0

    print("\n📘 Processing Statutory Laws (IPC / CrPC / CPC / IEA / NIA)...")

    for json_file in STATUTES_DIR.glob("*.json"):
        law_name = json_file.stem.upper()

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            section_count += 1

            section_no = entry.get("section") or entry.get("Section") or "Unknown"
            section_title = entry.get("section_title", "")
            section_text = entry.get("section_desc", "")

            full_text = clean_text(f"{section_title}. {section_text}")

            for i, chunk in enumerate(chunk_text(full_text)):
                processed.append({
                    "source": "statute",
                    "law": law_name,
                    "section": f"Section {section_no}",
                    "chunk_id": i,
                    "text": chunk
                })

    print(f"✅ Statutory sections processed: {section_count}")
    print(f"✅ Statute chunks generated: {len(processed)}")

    return processed


# --------------------------------------------------
# INDIC LEGAL QA
# --------------------------------------------------

def process_indic_legal_qa() -> List[Dict]:
    processed = []
    qa_count = 0

    print("\n❓ Processing IndicLegalQA Dataset...")

    for file in QA_DIR.glob("indic*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            qa_count += 1

            q = clean_text(item.get("question", ""))
            a = clean_text(item.get("answer", ""))

            if not q or not a:
                continue

            combined = f"Question: {q}\nAnswer: {a}"

            for i, chunk in enumerate(chunk_text(combined)):
                processed.append({
                    "source": "qa",
                    "dataset": "IndicLegalQA",
                    "chunk_id": i,
                    "text": chunk
                })

    print(f"✅ IndicLegalQA records loaded: {qa_count}")
    print(f"✅ IndicLegalQA chunks generated: {len(processed)}")

    return processed


# --------------------------------------------------
# INDIAN LAW QA (JSON ARRAY – Instruction / Response)
# --------------------------------------------------

def process_indian_law_qa_json() -> List[Dict]:
    processed = []
    record_count = 0

    print("\n📚 Processing Indian Law QA Dataset (JSON array)...")

    for file in QA_DIR.glob("*.json"):
        if "indian_law_qa" not in file.name.lower():
            continue

        with open(file, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        print(f"📂 Loaded {len(data)} QA records from {file.name}")

        for item in data:
            record_count += 1

            q = clean_text(item.get("Instruction", ""))
            a = clean_text(item.get("Response", ""))

            if not q or not a:
                continue

            combined = f"Question: {q}\nAnswer: {a}"

            for i, chunk in enumerate(chunk_text(combined)):
                processed.append({
                    "source": "qa",
                    "dataset": "IndianLawQA",
                    "chunk_id": i,
                    "text": chunk
                })

    print(f"✅ Indian Law QA records processed: {record_count}")
    print(f"✅ Indian Law QA chunks generated: {len(processed)}")

    return processed


# --------------------------------------------------
# PRE-CHUNKED SC TXT
# --------------------------------------------------

def process_sc_chunked_txt() -> List[Dict]:
    processed = []
    file_count = 0

    chunked_dir = JUDGMENTS_DIR.parent / "Indian_SC_Chunked"

    if not chunked_dir.exists():
        print("\nℹ️ No pre-chunked SC TXT folder found.")
        return processed

    print("\n📄 Processing Pre-Chunked Supreme Court TXT files...")

    for txt_file in chunked_dir.glob("*.txt"):
        file_count += 1
        with open(txt_file, "r", encoding="utf-8") as f:
            text = clean_text(f.read())

        processed.append({
            "source": "judgment_chunked",
            "origin": "huggingface",
            "file": txt_file.name,
            "text": text
        })

    print(f"✅ Pre-chunked SC files processed: {file_count}")
    print(f"✅ Pre-chunked SC chunks generated: {len(processed)}")

    return processed


# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------

def main():
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_chunks = []

    all_chunks.extend(process_sc_judgments())
    all_chunks.extend(process_statutes())
    all_chunks.extend(process_indic_legal_qa())
    all_chunks.extend(process_indian_law_qa_json())
    all_chunks.extend(process_sc_chunked_txt())

    output_path = PROCESSED_DATA_DIR / "legal_chunks.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print("\n🎉 PREPROCESSING COMPLETE")
    print(f"📦 TOTAL CHUNKS GENERATED: {len(all_chunks)}")
    print(f"📂 OUTPUT FILE: {output_path}")


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()
