"""
RAG (Retrieval-Augmented Generation) Pipeline
==============================================
Production-grade document processing pipeline using LangChain.

Architecture:
    PDF URL → Download → PyPDFLoader → TextSplitter → Embeddings → FAISS → Retriever → LLM Chain → JSON

Replaces the previous direct PDF-to-LLM approach with semantic retrieval,
improving accuracy, scalability, and cost efficiency.
"""

import os
import json
import logging
import tempfile
import hashlib
from typing import Optional

import requests
from dotenv import load_dotenv, find_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("rag_pipeline")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv(find_dotenv())

DEFAULT_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")
DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "1500"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "300"))
RETRIEVER_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

# Directory to cache downloaded PDFs and FAISS indices
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".rag_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


# ===========================================================================
# 1. DOCUMENT LOADER
# ===========================================================================

def download_pdf(url: str) -> str:
    """
    Download a PDF from *url* and return the local file path.
    Uses content-hash caching so the same PDF is never downloaded twice.
    """
    logger.info("⬇️  Downloading PDF from: %s", url)

    response = requests.get(url, timeout=60)
    response.raise_for_status()
    doc_bytes = response.content

    # Cache by content hash
    content_hash = hashlib.sha256(doc_bytes).hexdigest()[:16]
    local_path = os.path.join(CACHE_DIR, f"{content_hash}.pdf")

    if not os.path.exists(local_path):
        with open(local_path, "wb") as f:
            f.write(doc_bytes)
        logger.info("✅ PDF saved to cache: %s", local_path)
    else:
        logger.info("⚡ PDF cache hit: %s", local_path)

    return local_path


def load_pdf_documents(pdf_path: str):
    """
    Load a PDF and return a list of LangChain Document objects (one per page).
    """
    logger.info("📄 Loading PDF pages from: %s", pdf_path)
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    logger.info("📄 Loaded %d pages", len(documents))
    return documents


# ===========================================================================
# 2. TEXT SPLITTER
# ===========================================================================

def split_documents(documents, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
    """
    Split documents into smaller chunks suitable for embedding.
    Uses RecursiveCharacterTextSplitter which respects paragraph / sentence
    boundaries wherever possible.
    """
    logger.info(
        "✂️  Splitting %d documents (chunk_size=%d, overlap=%d)",
        len(documents), chunk_size, chunk_overlap,
    )
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_documents(documents)
    logger.info("✂️  Created %d chunks", len(chunks))
    return chunks


# ===========================================================================
# 3. EMBEDDINGS + 4. VECTOR STORE
# ===========================================================================

def _get_embeddings(model_name: str = DEFAULT_EMBEDDING_MODEL):
    """Return a HuggingFaceEmbeddings instance (local)."""
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )


def build_vector_store(chunks, api_key: str, embedding_model: str = DEFAULT_EMBEDDING_MODEL):
    """
    Convert document chunks into embeddings and store them in a FAISS index.

    Returns:
        FAISS vector store instance.
    """
    logger.info("🧠 Building vector store with %d chunks …", len(chunks))
    embeddings = _get_embeddings(embedding_model)
    vector_store = FAISS.from_documents(chunks, embeddings)
    logger.info("🧠 Vector store ready (%d vectors)", vector_store.index.ntotal)
    return vector_store


def save_vector_store(vector_store, index_name: str):
    """Persist a FAISS index to disk for reuse."""
    save_path = os.path.join(CACHE_DIR, index_name)
    vector_store.save_local(save_path)
    logger.info("💾 Vector store saved: %s", save_path)


def load_vector_store(index_name: str, api_key: str, embedding_model: str = DEFAULT_EMBEDDING_MODEL):
    """Load a previously saved FAISS index."""
    load_path = os.path.join(CACHE_DIR, index_name)
    if not os.path.exists(load_path):
        return None
    embeddings = _get_embeddings(embedding_model)
    return FAISS.load_local(load_path, embeddings, allow_dangerous_deserialization=True)


# ===========================================================================
# 5. RETRIEVER
# ===========================================================================

def get_retriever(vector_store, top_k: int = RETRIEVER_TOP_K):
    """
    Create a retriever that performs top-k semantic search over the
    vector store.
    """
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k},
    )
    logger.info("🔍 Retriever configured (top_k=%d)", top_k)
    return retriever


# ===========================================================================
# 6. LLM + CHAIN
# ===========================================================================

def _get_llm(api_key: str, model_name: str = DEFAULT_MODEL_NAME, temperature: float = 0.2):
    """Instantiate the Google Generative AI chat model via LangChain."""
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature,
        convert_system_message_to_human=True,
    )


# The meta-prompt wraps the user's domain-specific prompt with RAG context
_RAG_TEMPLATE = """You are an expert AI assistant. Use ONLY the following context extracted from a course document to answer the user's request. If the context does not contain enough information, use your best educational knowledge to fill gaps, but prioritise the document content.

=== RETRIEVED DOCUMENT CONTEXT ===
{context}
=== END CONTEXT ===

USER REQUEST:
{question}

IMPORTANT:
- Your response MUST be valid JSON matching the schema described in the user request.
- Do NOT include any text outside the JSON object.
- Do NOT wrap the JSON in markdown code fences.
"""


def build_rag_chain(
    vector_store,
    api_key: str,
    model_name: str = DEFAULT_MODEL_NAME,
    top_k: int = RETRIEVER_TOP_K,
):
    """
    Assemble the full RAG chain using LCEL:
        Retriever → Context Formatting → Prompt → LLM → Output Parser
    """
    retriever = get_retriever(vector_store, top_k)
    llm = _get_llm(api_key, model_name)

    prompt = PromptTemplate(
        template=_RAG_TEMPLATE,
        input_variables=["context", "question"],
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # The chain logic:
    # 1. Takes the user query (question)
    # 2. Passes it to the retriever to get context
    # 3. Formats those docs into a string
    # 4. Injects context and question into the prompt
    # 5. Sends prompt to LLM
    # 6. Parses LLM output to string
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    logger.info("⛓️  RAG chain assembled (LCEL version, model=%s)", model_name)
    return chain


# ===========================================================================
# 7. PUBLIC ENTRY POINT  (drop-in replacement for old gemini function)
# ===========================================================================

def process_document_with_rag(doc_link: str, prompt: str) -> str:
    """
    End-to-end RAG pipeline.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")

    # --- Step 1: Download ---
    pdf_path = download_pdf(doc_link)

    # --- Step 2: Load & Split ---
    documents = load_pdf_documents(pdf_path)
    chunks = split_documents(documents)

    if not chunks:
        raise ValueError("PDF produced zero text chunks.")

    # --- Step 3 & 4: Embed + Store ---
    content_bytes = open(pdf_path, "rb").read()
    content_hash = hashlib.sha256(content_bytes).hexdigest()[:16]
    index_name = f"index_{content_hash}"

    vector_store = load_vector_store(index_name, api_key)
    if vector_store is None:
        vector_store = build_vector_store(chunks, api_key)
        save_vector_store(vector_store, index_name)

    # --- Step 5: Build chain & invoke ---
    chain = build_rag_chain(vector_store, api_key)
    logger.info("🚀 Invoking RAG chain …")

    # In LCEL, we invoke with just the query string
    answer = chain.invoke(prompt)

    # --- Step 6: Clean up & validate JSON ---
    answer = _clean_json_response(answer)
    logger.info("✅ RAG pipeline complete")

    return answer


# ===========================================================================
# UTILITIES
# ===========================================================================

def _clean_json_response(text: str) -> str:
    """
    Strip markdown code fences and whitespace that the LLM sometimes adds
    around its JSON output.
    """
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def process_text_with_llm(prompt: str) -> str:
    """
    Lightweight helper for prompts that do NOT need document retrieval
    (e.g., quiz generation from structured topic data).

    Uses the same Gemini model via LangChain but skips the RAG retrieval
    steps entirely.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")

    llm = _get_llm(api_key)
    logger.info("🤖 Invoking LLM (text-only, no RAG) …")

    response = llm.invoke(prompt)
    answer = _clean_json_response(response.content)

    logger.info("✅ LLM response received — length: %d chars", len(answer))
    return answer
