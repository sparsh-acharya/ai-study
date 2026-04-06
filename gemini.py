"""
Document Processing Gateway
============================
Drop-in replacement that routes through the RAG pipeline.

The public function ``process_document_with_gemini`` is preserved so that
every existing caller (views.py, etc.) continues to work without changes.
Under the hood it now delegates to the RAG pipeline.
"""

import logging
from rag_pipeline import process_document_with_rag

logger = logging.getLogger("gemini")


def process_document_with_gemini(docLink: str, prompt: str) -> str:
    """
    Process a document using the RAG pipeline and return the response.

    This function maintains the same signature as the original so that
    ``views.py`` and any other caller can import and call it unchanged.

    Pipeline:
        PDF URL → Download → Chunk → Embed → FAISS → Retrieve → LLM → JSON

    Args:
        docLink: URL of the PDF document to process.
        prompt:  The domain-specific prompt (study-plan schema, etc.).

    Returns:
        str: Structured JSON response from the LLM.
    """
    logger.info("📨 process_document_with_gemini called — delegating to RAG pipeline")
    return process_document_with_rag(docLink, prompt)
