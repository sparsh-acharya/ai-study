# Fully corrected gemini.py file

from dotenv import load_dotenv, find_dotenv
import os
import requests
import google.generativeai as genai

def process_document_with_gemini(docLink: str, prompt: str) -> str:
    """
    Process a document using the Gemini API and return the response.

    Args:
        docLink (str): URL of the document to process.
        prompt (str): The prompt to send to the Gemini API.

    Returns:
        str: The response from the Gemini API.
    """
    try:
        # Load environment variables
        load_dotenv(find_dotenv())
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # 1. Configure the API key (the modern way)
        genai.configure(api_key=GEMINI_API_KEY)

        # Download the file content
        print(f"Downloading document from: {docLink}")
        response = requests.get(docLink)
        response.raise_for_status()  # This will raise an error for bad responses (4xx or 5xx)
        doc_bytes = response.content
        print("Document downloaded successfully.")

        # 2. Prepare the document part for the API
        pdf_file = {"mime_type": "application/pdf", "data": doc_bytes}

        # 3. Instantiate the model and generate content
        # Use available model names from the API
        model_names = [
            "gemini-flash-latest",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-pro-latest"
        ]

        model = None
        for model_name in model_names:
            try:
                print(f"Trying model: {model_name}")
                model = genai.GenerativeModel(model_name)

                # Test the model with a simple request first
                model.generate_content("Hello")
                print(f"Successfully initialized model: {model_name}")
                break
            except Exception as e:
                print(f"Failed to initialize model {model_name}: {str(e)}")
                continue

        if model is None:
            raise ValueError("Could not initialize any Gemini model. Please check your API key and model availability.")

        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )

        response = model.generate_content(
            [pdf_file, prompt],
            generation_config=generation_config
        )

        return response.text

    except Exception as e:
        print(f"Error in process_document_with_gemini: {str(e)}")
        raise e