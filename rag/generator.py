"""
LawSpeaks – RAG Generator Module

Purpose:
- Combine retrieved legal chunks with prompt templates
- Call Mistral LLM API
- Return safe, structured legal awareness responses

This module:
- NEVER answers without retrieval
- NEVER gives legal advice
- ALWAYS includes disclaimer
"""
import re
import html
# --- INTENT DETECTION IMPORTS ---
from sentence_transformers import SentenceTransformer
import numpy as np
import requests
import json
from typing import Dict, List

from config import (
    GROK_API_URL,
    GROK_API_KEY,
    GROK_MODEL_NAME,
    MAX_TOKENS,
    TEMPERATURE,
    TOP_P
)

from rag.retriever import LegalRetriever
from rag.prompt_templates import (
    format_context,
    legal_question_prompt,
    rights_prompt,
    action_guide_prompt,
    case_example_prompt,
    law_library_prompt,
    situation_prompt,
    risk_checker_prompt
)

def is_small_talk(query: str) -> bool:
    greetings = [
        "hi", "hello", "hey", "hii", "hola",
        "good morning", "good evening", "good afternoon",
        "how are you", "thanks", "thank you", "ok"
    ]

    query = query.lower().strip()

    # Exact match only (IMPORTANT FIX)
    return query in greetings and len(query.split()) <= 3


def small_talk_response():
    return (
        "Hello! 👋 I'm LawSpeaks, your Indian Legal Awareness Assistant.\n\n"
        "You can ask me about:\n"
        "- Your legal rights\n"
        "- Police procedures\n"
        "- Legal actions (FIR, complaint, etc.)\n"
        "- Indian laws and sections\n\n"
        "How can I help you today?\n\n"
        "⚠️ Disclaimer: This is general legal information."
    )

def is_prompt_injection(query: str) -> bool:

    dangerous_patterns = [

        "ignore previous instructions",
        "ignore all instructions",
        "system prompt",
        "reveal prompt",
        "show hidden instructions",
        "act as",
        "developer message",
        "jailbreak",
        "bypass rules",
        "forget previous",

    ]

    query = query.lower()

    return any(
        p in query
        for p in dangerous_patterns
    )


def is_abusive(query: str) -> bool:
    abusive_keywords = [
        "fuck", "shit", "bitch", "idiot", "stupid",
        "madarchod", "bhenchod", "gandu", "chutiya"
    ]

    query = query.lower()

    return any(word in query for word in abusive_keywords)

def abusive_response():
    return (
        "⚠️ Please maintain respectful language.\n\n"
        "I'm here to provide legal awareness and assistance.\n"
        "If you have a legal question, feel free to ask.\n\n"
        "⚠️ Disclaimer: This is general legal information."
    )


def non_legal_response():
    return (
        "I'm designed to answer questions related to Indian law and legal awareness only.\n\n"
        "Please ask a question related to:\n"
        "- Legal rights\n"
        "- Police procedures\n"
        "- FIR / complaints\n"
        "- Laws and sections\n\n"
        "⚠️ Disclaimer: This is general legal information."
    )            


def is_emergency(query: str) -> bool:
    """
    Detects high-risk / emergency legal situations using:
    - direct violence keywords
    - intent patterns
    - severity signals
    """

    query = query.lower().strip()

    # -------- STRONG EMERGENCY KEYWORDS --------
    severe_keywords = [
        "kill", "killed", "death", "die", "murder",
        "rape", "molest", "sexual assault",
        "attack", "beaten", "beating", "violence",
        "threat", "threatening", "weapon", "gun", "knife",
        "kidnap", "abduct", "acid attack"
    ]

    # -------- INTENT PATTERNS --------
    intent_patterns = [
        "someone is trying to",
        "someone tried to",
        "what if someone",
        "if someone",
        "i am being",
        "he is beating",
        "they attacked me"
    ]

    # -------- URGENCY SIGNALS --------
    urgency_words = [
        "urgent", "immediately", "right now",
        "help", "save me", "danger", "serious"
    ]

    # -------- CHECK LOGIC --------
    severe_match = any(word in query for word in severe_keywords)
    intent_match = any(pattern in query for pattern in intent_patterns)
    urgency_match = any(word in query for word in urgency_words)

    # Strong condition
    if severe_match:
        return True

    # Medium condition (intent + urgency)
    if intent_match and urgency_match:
        return True

    return False

def build_emergency_prefix():
    return (
        "🚨 EMERGENCY ALERT\n\n"
        "This situation appears serious and may involve immediate risk.\n\n"
        "👉 If you are in danger right now:\n"
        "- Call Police: 100 or 112\n"
        "- Seek immediate help from nearby people\n"
        "- Move to a safe location\n\n"
    )


def extract_sections_from_context(chunks):
    sections = set()

    for chunk in chunks:
        sec = chunk.get("section")
        law = chunk.get("law")

        # ✅ Primary: metadata
        if sec and law:
            sections.add(f"{law} Section {sec}")
            continue

        # 🔥 SAFE FALLBACK (controlled regex)
        text = chunk.get("text", "")

        matches = re.findall(r"(IPC|CrPC|Article)\s*\d+[A-Z]*", text)

        for m in matches:
            sections.add(m.strip())

    return list(sections)


def is_law_query(query: str) -> bool:
    keywords = [
        "section", "ipc", "crpc", "article",
        "act", "law", "code", "constitution"
    ]

    query = query.lower()

    return any(word in query for word in keywords)

def is_case_query(query: str) -> bool:
    keywords = [
        "case", "judgement", "judgment",
        "vs", "v.", "court decision",
        "example case", "real case"
    ]

    query = query.lower()

    return any(word in query for word in keywords)


# --------------------------------------------------
# GENERATOR CLASS
# --------------------------------------------------

class LegalRAGGenerator:
    """
    Main RAG generator class for LawSpeaks.
    """

    def __init__(self):
        self.retriever = LegalRetriever()

        # -------------------------------
        # LEGAL INTENT DETECTION SETUP
        # -------------------------------

        print("Loading Intent Model...")

        self.intent_model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        print("Intent Model Loaded")

        # 🔥 VERY DETAILED LEGAL INTENT BANK
        self.legal_intents = [

            # --- CRIME / VIOLENCE ---
            "someone hit me",
            "someone attacked me",
            "physical assault happened",
            "fight in public",
            "someone beat me",
            "violence against me",
            "domestic violence case",
            "husband beating wife",
            "family abuse situation",

            # --- ROAD / ACCIDENT ---
            "road accident case",
            "hit and run case",
            "vehicle accident law",
            "car accident issue",
            "bike accident problem",
            "someone hit me with vehicle",
            "accident and driver ran away",
            "rash driving case",
            "negligent driving issue",
            "traffic accident legal help",
            "motor vehicle accident case",
            "injury due to accident",
            "road safety violation",

            # --- POLICE / ARREST ---
            "police arrested me",
            "police took me without warrant",
            "illegal arrest situation",
            "police harassment",
            "custody rights",
            "what happens after arrest",
            "police asking for bribe",

            # --- THREAT / INTIMIDATION ---
            "someone threatened me",
            "death threat received",
            "blackmail situation",
            "extortion case",
            "someone forcing me",
            "intimidation problem",

            # --- PROPERTY / LAND ---
            "land dispute issue",
            "property conflict",
            "neighbor encroachment",
            "illegal possession of land",
            "ownership dispute",
            "tenant landlord issue",
            "eviction without notice",
            "rent dispute problem",

            # --- WORKPLACE / SALARY ---
            "salary not paid",
            "company not paying wages",
            "workplace harassment",
            "boss abusing employee",
            "termination without reason",
            "labor law issue",

            # --- CYBER / ONLINE ---
            "cyber crime issue",
            "online fraud happened",
            "someone hacked my account",
            "cyber bullying case",
            "fake profile harassment",
            "online scam problem",
            "upi fraud case",
            "bank fraud issue",

            # --- WOMEN / SAFETY ---
            "molestation case",
            "sexual harassment",
            "stalking issue",
            "dowry harassment",
            "outraging modesty",
            "rape case",
            "eve teasing incident",

            # --- RIGHTS ---
            "what are my rights",
            "legal rights in india",
            "citizen rights",
            "fundamental rights issue",
            "right to privacy problem",

            # --- LEGAL PROCEDURE ---
            "how to file fir",
            "how to file complaint",
            "legal procedure steps",
            "court process",
            "bail procedure",
            "legal action steps",

            # --- FAMILY LAW ---
            "divorce case",
            "child custody issue",
            "maintenance problem",
            "alimony dispute",
            "marriage law issue",

            # --- GENERAL LEGAL ---
            "is this legal",
            "what law says",
            "legal problem help",
            "law related issue",
            "punishment for crime",
        ]

        self.intent_embeddings = self.intent_model.encode(
            self.legal_intents,
            normalize_embeddings=True
        )


    def is_legal_query_semantic(self, query: str) -> bool:
        try:
            query_emb = self.intent_model.encode(
                [query],
                normalize_embeddings=True
            )[0]

            similarities = np.dot(self.intent_embeddings, query_emb)

            max_score = float(np.max(similarities))

            return max_score > 0.40 # tune 0.4–0.6

        except Exception:
            return False


    def keyword_legal_check(self, query: str) -> bool:
        query = query.lower()

        legal_keywords = [

            # core
            "law", "legal", "court", "judge", "lawyer",

            # police
            "police", "arrest", "custody", "fir", "complaint",

            # crime
            "crime", "offence", "punishment", "illegal",

            # violence
            "hit", "attack", "beat", "abuse", "violence",

            # threats
            "threat", "blackmail", "extortion",

            # property
            "land", "property", "rent", "tenant", "eviction",

            # work
            "salary", "wages", "job", "company", "boss",

            # cyber
            "fraud", "scam", "hack", "cyber", "online",

            # women safety
            "harassment", "molest", "rape", "stalk",

            # procedure
            "bail", "case", "section", "ipc", "crpc",

            # rights
            "rights", "privacy", "constitution"
        ]

        return any(word in query for word in legal_keywords)


    def simplify_query(self, query: str) -> str:
        """
        Convert long user story into short legal query
        """
        prompt = f"""
    Convert this user statement into a short legal search query.

    Focus on:
    - main issue
    - legal keywords
    - keep it under 10 words

    User:
    {query}

    Output only the simplified query.
    """

        try:
            result = self._call_grok(prompt)
            return result.strip()
        except:
            return query  # fallback

    def is_legal_query(self, query: str) -> bool:

        # 1. Keyword check (fast)
        if self.keyword_legal_check(query):
            return True

        # 2. Semantic check (main)
        if self.is_legal_query_semantic(query):
            return True

        return False
    # --------------------------------------------------
    # MISTRAL API CALL
    # --------------------------------------------------

    def _call_grok(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {GROK_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": GROK_MODEL_NAME,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "max_tokens": MAX_TOKENS
        }

        print("Calling Groq API...")
        try:
            response = requests.post(
                GROK_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            print("Groq Response Received")
            return data["choices"][0]["message"]["content"]

        except Exception as e:

            print("=" * 60)
            print("GROQ API ERROR")
            print(str(e))
            print("=" * 60)

            return (
                "⚠️ System error while generating response.\n\n"
                "Please try again later.\n\n"
                "⚠️ Disclaimer: This is general legal information."
            )
    # --------------------------------------------------
    # COMMON PIPELINE
    # --------------------------------------------------

    def classify_intent(self, query: str) -> str:
        """
        LLM-based intent classification
        Returns: LEGAL / NON_LEGAL / UNSAFE
        """

        prompt = f"""
    Classify the user query into ONE category:

    1. LEGAL → real-life problems, rights, crime, disputes, safety
    2. NON_LEGAL → movies, entertainment, random topics
    3. UNSAFE → abusive or offensive language

    ONLY return ONE WORD:
    LEGAL or NON_LEGAL or UNSAFE

    Query:
    {query}
    """

        try:
            result = self._call_grok(prompt).strip().upper()

            if "UNSAFE" in result:
                return "UNSAFE"
            elif "LEGAL" in result:
                return "LEGAL"
            else:
                return "NON_LEGAL"

        except:
            return "LEGAL"


    def expand_query(self, query: str):
        return [
            query,
            f"indian law {query}",
            f"legal issue india {query}",
            f"rights related to {query}"
        ]

    def is_ambiguous(self, query: str) -> bool:
        vague_words = ["problem", "issue", "help", "something", "matter"]

        if len(query.split()) < 4:
            return True

        if any(word in query.lower() for word in vague_words):
            return True

        return False

    def _generate(self, user_input: str, prompt_builder, strict_legal=True) -> str:
        """
        Shared generation logic:
        - Retrieve
        - Format context
        - Build prompt
        - Call LLM
        """
        # -------- FILTER LAYER --------
        if is_prompt_injection(user_input):

            return (
                "⚠️ Invalid request.\n\n"
                "LawSpeaks only answers legal awareness queries."
            )

        # 2. Abusive language
        if is_abusive(user_input):
            return abusive_response()

        # 1. Small talk
        if is_small_talk(user_input):
            return small_talk_response()

        # -------- EMERGENCY DETECTION (FIX) --------
        # 🚨 disable emergency for case feature
        if "case" in user_input.lower() or "judgement" in user_input.lower():
            emergency_flag = False
        else:
            emergency_flag = is_emergency(user_input)

        # -------- NON-LEGAL FILTER (ADD HERE) --------
        if strict_legal and not self.is_legal_query(user_input):
            return non_legal_response()

        # -------- INTENT CLASSIFICATION --------
        intent = self.classify_intent(user_input)

        if intent == "UNSAFE":
            return abusive_response()

        if strict_legal and intent == "NON_LEGAL":
            return non_legal_response()

        


        # -------- QUERY SIMPLIFICATION --------
        simplified_query = user_input

        # fallback protection
        if not simplified_query or len(simplified_query.split()) < 2:
            simplified_query = user_input

        queries = []

        queries.extend(self.expand_query(user_input))        # original
        queries.extend(self.expand_query(simplified_query))  # simplified

        all_chunks = []

        for q in queries:
            chunks = self.retriever.retrieve(q)
            all_chunks.extend(chunks)

        # remove duplicates
        unique_chunks = {chunk["text"]: chunk for chunk in all_chunks}
        retrieved_chunks = list(unique_chunks.values())

        import logging

        print("=" * 50)
        print("Retrieved Chunks:", len(retrieved_chunks))
        print("=" * 50)

        for chunk in retrieved_chunks[:2]:
            logging.warning(f"DEBUG SAMPLE: {chunk}")

        if not retrieved_chunks:

            if self.is_ambiguous(user_input):
                return (
                    "Your question is unclear.\n\n"
                    "👉 Please provide more details like:\n"
                    "- What exactly happened?\n"
                    "- Who is involved?\n\n"
                    "This helps in giving accurate legal information.\n\n"
                    "⚠️ Disclaimer: This is general legal information."
                )

            return (
                "⚠️ I do not have enough verified legal information to answer this accurately.\n\n"
                "👉 Please try:\n"
                "- Rephrasing your question\n"
                "- Adding more details\n\n"
                "⚠️ Disclaimer: This is general legal information."
            )

        sections = extract_sections_from_context(retrieved_chunks)

        # -------- HARD FALLBACK LAW (IMPORTANT) --------
        if not sections:
            user_lower = user_input.lower()

            if "accident" in user_lower or "hit" in user_lower:
                sections = ["IPC Section 279", "IPC Section 304A"]

            elif "threat" in user_lower:
                sections = ["IPC Section 503", "IPC Section 506"]

            elif "salary" in user_lower or "wages" in user_lower:
                sections = ["Payment of Wages Act"]

            elif "follow" in user_lower or "stalking" in user_lower:
                sections = ["IPC Section 354D"]

        context = format_context(retrieved_chunks)
        prompt = prompt_builder(context, sections)
        

        response = self._call_grok(prompt)

        # -------- EMERGENCY HANDLING --------
        if emergency_flag:
            response = build_emergency_prefix() + response

        return response

    # --------------------------------------------------
    # FEATURE 1: ASK A LEGAL QUESTION
    # --------------------------------------------------

    def ask_legal_question(self, query: str) -> str:
        return self._generate(
            query,
            lambda context, sections: legal_question_prompt(query, context, sections),
            strict_legal=True
        )

    # --------------------------------------------------
    # FEATURE 2: KNOW YOUR RIGHTS
    # --------------------------------------------------

    def know_your_rights(self, category: str) -> str:
        enhanced_category = f"Indian legal rights related to {category} (India specific, practical user protections)"

        return self._generate(
            enhanced_category,
            lambda context, sections: rights_prompt(enhanced_category, context)
        )

    # --------------------------------------------------
    # FEATURE 3: LEGAL ACTION GUIDE
    # --------------------------------------------------

    def legal_action_guide(self, action_type: str) -> str:
        return self._generate(
            action_type,
            lambda context, sections: action_guide_prompt(action_type, context)
        )

    # --------------------------------------------------
    # FEATURE 4: CASE EXAMPLES
    # --------------------------------------------------

    def case_examples(self, issue: str) -> str:
        # -------- STRICT FILTER --------
        if not is_case_query(issue):
            return (
                "⚠️ Please enter a valid case-related query.\n\n"
                "Examples:\n"
                "- Theft case example\n"
                "- Supreme Court judgement on murder\n"
                "- Landmark case for privacy\n\n"
                "This section only provides real case examples.\n\n"
                "⚠️ Disclaimer: This is general legal information."
            )

        # -------- QUERY VARIATION (KEY FIX) --------
        import random

        variations = [
            issue,
            issue + " indian supreme court judgement",
            issue + " landmark judgement india",
            issue + " criminal case judgement india"
        ]

        varied_query = random.choice(variations)

        response = self._generate(
            varied_query,
            lambda context, sections: case_example_prompt(issue, context)
        )

        # 🔥 SAFETY FILTER (CRITICAL)
        if "_" in response or "vs_" in response.lower():
            return (
                "⚠️ I could not find sufficiently reliable case examples for this query.\n\n"
                "👉 Please try a more specific query like:\n"
                "- murder case example\n"
                "- dowry death case\n"
                "- theft court case\n\n"
                "⚠️ Disclaimer: This is general legal information."
            )

        return response

    # --------------------------------------------------
    # FEATURE 5: LAW LIBRARY
    # --------------------------------------------------

    def law_library(self, law_query: str) -> str:
        # -------- STRICT FILTER --------
        if not is_law_query(law_query):
            return (
                "⚠️ Please enter a valid law or section query.\n\n"
                "Examples:\n"
                "- IPC Section 420\n"
                "- Article 21\n"
                "- CrPC Section 154\n\n"
                "This section is only for law/section reference.\n\n"
                "⚠️ Disclaimer: This is general legal information."
            )

        return self._generate(
            law_query,
            lambda context, sections: law_library_prompt(law_query, context)
        )

    # --------------------------------------------------
    # FEATURE 6: MY LEGAL SITUATION
    # --------------------------------------------------

    def my_legal_situation(self, situation_details: str) -> str:
        return self._generate(
            situation_details,
            lambda context, sections: situation_prompt(situation_details, context),
            strict_legal=False
        )

    # --------------------------------------------------
    # FEATURE 7: RISK & URGENCY CHECKER
    # --------------------------------------------------

    def risk_and_urgency(self, issue: str) -> str:
        return self._generate(
            issue,
            lambda context, sections: risk_checker_prompt(issue, context),
            strict_legal=False
        )


# --------------------------------------------------
# OPTIONAL LOCAL TEST
# --------------------------------------------------

if __name__ == "__main__":
    generator = LegalRAGGenerator()
    response = generator.ask_legal_question(
        "Police refused to register FIR for theft"
    )
    print("\n🧠 LawSpeaks RESPONSE:\n")
    print(response)
