#!/usr/bin/env python3
"""
Test script to verify the RAG pipeline end-to-end.

Usage:
    python test_gemini.py                  # Runs all tests
    python test_gemini.py --quick          # Only tests API connectivity
"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv, find_dotenv


def test_api_connectivity():
    """Test 1: Verify API key & basic Gemini connectivity via LangChain."""
    print("\n" + "=" * 60)
    print("TEST 1: API Connectivity")
    print("=" * 60)

    load_dotenv(find_dotenv())
    api_key = os.getenv("GEMINI_API_KEY")

    print(f"  API Key loaded: {'✅ Yes' if api_key else '❌ No'}")
    if not api_key:
        print("  ❌ GEMINI_API_KEY not found in .env")
        return False

    print(f"  API Key preview: {api_key[:10]}…{api_key[-4:]}")

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0,
        )
        response = llm.invoke("Say hello in one sentence.")
        print(f"  ✅ LLM response: {response.content[:80]}…")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_embeddings():
    """Test 2: Verify embedding model works."""
    print("\n" + "=" * 60)
    print("TEST 2: Embedding Model")
    print("=" * 60)

    load_dotenv(find_dotenv())
    api_key = os.getenv("GEMINI_API_KEY")

    try:
        from langchain_huggingface import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
        )
        vector = embeddings.embed_query("machine learning fundamentals")
        print(f"  ✅ Embedding vector dimension: {len(vector)}")
        print(f"  ✅ First 5 values: {vector[:5]}")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_text_llm():
    """Test 3: Verify the text-only LLM helper (used by quiz generator)."""
    print("\n" + "=" * 60)
    print("TEST 3: Text-Only LLM (Quiz Generator Path)")
    print("=" * 60)

    try:
        from rag_pipeline import process_text_with_llm

        prompt = """Generate a simple JSON object with this structure:
{"greeting": "hello", "status": "working"}
Output ONLY valid JSON, no other text."""

        response = process_text_with_llm(prompt)
        data = json.loads(response)
        print(f"  ✅ Response parsed: {data}")
        return True
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON parse failed: {e}")
        print(f"  Raw response: {response}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_full_rag_pipeline():
    """Test 4: Full RAG pipeline with a sample PDF URL."""
    print("\n" + "=" * 60)
    print("TEST 4: Full RAG Pipeline (End-to-End)")
    print("=" * 60)

    try:
        from rag_pipeline import (
            download_pdf,
            load_pdf_documents,
            split_documents,
            build_vector_store,
            get_retriever,
        )

        # Use a publicly available small PDF for testing
        test_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"

        print("  Step 1: Downloading PDF …")
        pdf_path = download_pdf(test_url)
        print(f"    ✅ Downloaded to: {pdf_path}")

        print("  Step 2: Loading pages …")
        docs = load_pdf_documents(pdf_path)
        print(f"    ✅ Pages loaded: {len(docs)}")

        print("  Step 3: Splitting into chunks …")
        chunks = split_documents(docs)
        print(f"    ✅ Chunks created: {len(chunks)}")

        if not chunks:
            print("    ⚠️  PDF has no extractable text — skipping vector store test")
            return True

        load_dotenv(find_dotenv())
        api_key = os.getenv("GEMINI_API_KEY")

        print("  Step 4: Building vector store …")
        store = build_vector_store(chunks, api_key)
        print(f"    ✅ Vectors stored: {store.index.ntotal}")

        print("  Step 5: Testing retriever …")
        retriever = get_retriever(store, top_k=2)
        results = retriever.invoke("What is this document about?")
        print(f"    ✅ Retrieved {len(results)} chunks")

        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Test the RAG pipeline")
    parser.add_argument("--quick", action="store_true", help="Run only API connectivity test")
    args = parser.parse_args()

    print("🧪 RAG Pipeline Test Suite")
    print("=" * 60)

    results = {}

    results["API Connectivity"] = test_api_connectivity()

    if not args.quick:
        results["Embeddings"] = test_embeddings()
        results["Text LLM"] = test_text_llm()
        results["Full RAG Pipeline"] = test_full_rag_pipeline()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    all_pass = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {name}")
        if not passed:
            all_pass = False

    print("=" * 60)
    if all_pass:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed — check output above for details")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
