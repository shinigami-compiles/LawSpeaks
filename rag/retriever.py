"""
LawSpeaks – FAISS Retriever Module

Purpose:
- Convert user query to embedding
- Perform semantic search over FAISS index
- Return top-k relevant legal chunks with metadata

Used by:
- generator.py
- FastAPI endpoints

This module NEVER performs reasoning.
It only retrieves verified legal context.
"""
import random
import json
import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict

from sentence_transformers import SentenceTransformer
from sentence_transformers import CrossEncoder

from config import (
    FAISS_INDEX_PATH,
    FAISS_METADATA_PATH,
    EMBEDDING_MODEL_NAME,
    FAISS_TOP_K
)

# --------------------------------------------------
# RETRIEVER CLASS
# --------------------------------------------------

class LegalRetriever:
    """
    FAISS-based semantic retriever for legal documents.
    """

    def __init__(self):
        """
        Load FAISS index, metadata, and embedding model.
        """
        self._load_index()
        self._load_metadata()
        self._load_embedding_model()

        try:
            self.reranker = CrossEncoder(
                "cross-encoder/ms-marco-MiniLM-L-6-v2"
            )
            self.reranker_available = True

        except Exception as e:
            print("WARNING: CrossEncoder disabled")
            print(str(e))

            self.reranker = None
            self.reranker_available = False

    # --------------------------------------------------

    def _load_index(self):
        """
        Loads FAISS index from disk.
        """
        if not FAISS_INDEX_PATH.exists():
            raise FileNotFoundError(
                "FAISS index not found. "
                "Run build_faiss_index.py first."
            )

        self.index = faiss.read_index(str(FAISS_INDEX_PATH))
        print("FAISS Index Loaded")
        print("Vectors:", self.index.ntotal)

    # --------------------------------------------------

    def _load_metadata(self):
        """
        Loads metadata corresponding to FAISS vectors.
        """
        if not FAISS_METADATA_PATH.exists():
            raise FileNotFoundError(
                "FAISS metadata not found. "
                "Run build_faiss_index.py first."
            )

        with open(FAISS_METADATA_PATH, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
            print("Metadata Loaded")
            print("Chunks:", len(self.metadata))

    # --------------------------------------------------

    def _load_embedding_model(self):
        """
        Loads MiniLM sentence transformer model.
        """
        print("Loading MiniLM Model...")

        self.model = SentenceTransformer(
            EMBEDDING_MODEL_NAME
        )

        print("MiniLM Loaded")

    # --------------------------------------------------
    # MAIN RETRIEVAL FUNCTION
    # --------------------------------------------------

    def retrieve(self, query: str, top_k: int = FAISS_TOP_K) -> List[Dict]:
        """
        Retrieves top-k most relevant legal chunks for a query.

        Args:
            query (str): User legal query
            top_k (int): Number of results to return

        Returns:
            List of metadata dictionaries with legal text
        """

        if not query or not query.strip():
            return []

        # Embed query
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype("float32")

        # FAISS similarity search
        # Get more candidates for reranking
        distances, indices = self.index.search(query_embedding, top_k * 5)

        SIMILARITY_THRESHOLD = 0.25  # start here

        filtered_candidates = []

        for dist, idx in zip(distances[0], indices[0]):
            similarity = 1 - dist  # normalized embeddings

            if similarity >= SIMILARITY_THRESHOLD:
                filtered_candidates.append(self.metadata[idx])

        candidates = filtered_candidates

        if not candidates:
            # 🔥 fallback: take top raw results without threshold
            fallback_candidates = []

            for idx in indices[0][:top_k]:
                if idx < len(self.metadata):
                    fallback_candidates.append(self.metadata[idx])

            candidates = fallback_candidates

        print("Retrieved candidates count:", len(candidates))
        # -------- RERANKING --------
        pairs = [(query, c["text"]) for c in candidates]

        if self.reranker_available:

            scores = self.reranker.predict(pairs)

            for i, score in enumerate(scores):
                candidates[i]["score"] = float(score)

            for c in candidates:
                if c.get("source") == "statute":
                    c["score"] += 1.5

            reranked = sorted(
                candidates,
                key=lambda x: x["score"],
                reverse=True
            )

        else:

            reranked = candidates

        # -------- DIVERSITY BOOST --------
        top_candidates = reranked[:top_k * 3]

        # Shuffle slightly to avoid repetition
        random.shuffle(top_candidates)

        # -------- FORCE INCLUDE STATUTES --------
        statute_chunks = [c for c in reranked if c.get("source") == "statute"]

        final_results = []

        # always include statutes first
        final_results.extend(statute_chunks[:2])

        # fill remaining
        for c in reranked:
            if c not in final_results:
                final_results.append(c)
            if len(final_results) >= top_k:
                break

        return final_results[:top_k]


# --------------------------------------------------
# SIMPLE CLI TEST (OPTIONAL)
# --------------------------------------------------

if __name__ == "__main__":
    retriever = LegalRetriever()
    query = "Police refused to file FIR"
    results = retriever.retrieve(query)

    print("\n🔎 Retrieved Legal Chunks:\n")
    for r in results:
        print("-" * 80)
        print(r.get("text", "")[:500])
